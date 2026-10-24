"""Optional reversible transport for the frozen PUBLIC-DATA state reference."""
from dataclasses import dataclass
import json
import re
import zlib

from baseline import state_reference as host

ZLIB_MAGIC = b"SMTZ1\x00"
BITMAP_ENCODING = "smt-default-bitmap-v1"
MODES = ("full", "bitmap", "zlib")
DEFAULT_HEX = tuple(x.hex() for x in host.DEFAULTS[:host.DEPTH])


class WireError(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    max_wire_bytes: int = 8 * 1024 * 1024
    max_plain_bytes: int = 8 * 1024 * 1024
    max_steps: int = 256
    max_key_bytes: int = 4096

    def __post_init__(self):
        if any(type(v) is not int or v < 0 for v in (self.max_wire_bytes, self.max_plain_bytes, self.max_steps, self.max_key_bytes)):
            raise ValueError("limits must be nonnegative integers")


def _canonical(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _hex_array_size(count):
    # Brackets, 64 hex characters plus quotes per node, and separators.
    return 2 + 66 * count + max(0, count - 1)


_ENCODING_OVERHEAD = len(_canonical({"encoding": BITMAP_ENCODING})) - 1
_BITMAP_OVERHEAD = len(_canonical({"bitmap": "0" * 64})) - 1


def _mode(mode):
    if type(mode) is not str or mode not in MODES:
        raise WireError("unknown transport mode")


def encode_batch(batch, mode="full"):
    """Default path is exactly the frozen encoder. No keys/randomness are used.

    All experimental modes start with that same byte string. Encoding does not
    authenticate a batch; receiving limits and cryptographic checks are separate.
    """
    _mode(mode)
    full = host.serialized_batch(batch)
    if mode == "full":
        return full
    if mode == "zlib":
        return ZLIB_MAGIC + zlib.compress(full, level=6)
    body = json.loads(full)
    body["encoding"] = BITMAP_ENCODING
    for step in body["steps"]:
        if len(step["siblings"]) != host.DEPTH:
            raise WireError("invalid source proof length")
        mask, saved = 0, []
        for level, value in enumerate(step["siblings"]):
            if value != DEFAULT_HEX[level]:
                mask |= 1 << level
                saved.append(value)
        step["bitmap"] = f"{mask:064x}"
        step["siblings"] = saved
    return _canonical(body)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WireError("duplicate JSON field")
        result[key] = value
    return result


def _constant(value):
    raise WireError("non-finite JSON number")


def _fields(body, fields):
    if type(body) is not dict or set(body) != set(fields):
        raise WireError("missing or unknown fields")


def _hex(value, size=None, maximum=None):
    if type(value) is not str or len(value) % 2:
        raise WireError("invalid hex type/length")
    if size is not None and len(value) != 2 * size:
        raise WireError("wrong hex size")
    if maximum is not None and len(value) > 2 * maximum:
        raise WireError("oversized hex value")
    if re.fullmatch(r"[0-9a-f]*", value) is None:
        raise WireError("noncanonical hex")
    return bytes.fromhex(value)


def _checkpoint(body):
    _fields(body, ("session", "epoch", "root", "size"))
    if type(body["session"]) is not str or not 1 <= len(body["session"]) <= 256:
        raise WireError("invalid session")
    for field in ("epoch", "size"):
        if type(body[field]) is not int or not 0 <= body[field] < 2**64:
            raise WireError("invalid nonnegative uint64")
    return host.Checkpoint(body["session"], body["epoch"], _hex(body["root"], 32), body["size"])


def _bounded_inflate(wire, limits):
    if not wire.startswith(ZLIB_MAGIC):
        raise WireError("wrong zlib envelope")
    decoder = zlib.decompressobj()
    plain = decoder.decompress(wire[len(ZLIB_MAGIC):], limits.max_plain_bytes + 1)
    if len(plain) > limits.max_plain_bytes:
        raise WireError("decompression limit exceeded")
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise WireError("truncated stream, trailing data, or concatenated streams")
    return plain


def decode_batch(wire, mode="full", limits=Limits()):
    """Parse the shared transport profile. This function does not verify a signature."""
    _mode(mode)
    try:
        if type(wire) is not bytes or len(wire) > limits.max_wire_bytes:
            raise WireError("wire type or size limit")
        plain = _bounded_inflate(wire, limits) if mode == "zlib" else wire
        if mode != "bitmap" and len(plain) > limits.max_plain_bytes:
            raise WireError("plain size limit")
        body = json.loads(plain.decode("ascii"), object_pairs_hook=_pairs, parse_constant=_constant)
        required = ("domain", "previous", "next", "steps", "signature")
        _fields(body, required + (("encoding",) if mode == "bitmap" else ()))
        if body["domain"] != host.DOMAIN.decode("ascii"):
            raise WireError("domain mismatch")
        if mode == "bitmap" and body["encoding"] != BITMAP_ENCODING:
            raise WireError("unknown bitmap format")
        if _canonical(body) != plain:
            raise WireError("noncanonical JSON")
        previous, next_checkpoint = _checkpoint(body["previous"]), _checkpoint(body["next"])
        signature = _hex(body["signature"], 64)
        if type(body["steps"]) is not list or not 1 <= len(body["steps"]) <= limits.max_steps:
            raise WireError("step count out of bounds")
        parsed = []
        restored_size = len(plain) - _ENCODING_OVERHEAD if mode == "bitmap" else len(plain)
        for step in body["steps"]:
            _fields(step, ("operation", "key", "siblings") + (("bitmap",) if mode == "bitmap" else ()))
            if type(step["operation"]) is not str or step["operation"] not in ("add", "remove"):
                raise WireError("invalid operation")
            key = _hex(step["key"], maximum=limits.max_key_bytes)
            if type(step["siblings"]) is not list or len(step["siblings"]) > host.DEPTH:
                raise WireError("invalid sibling array")
            saved = tuple(_hex(s, 32) for s in step["siblings"])
            if mode == "bitmap":
                mask = int.from_bytes(_hex(step["bitmap"], 32), "big")
                if mask.bit_count() != len(saved):
                    raise WireError("bitmap/node count mismatch")
                restored_size += _hex_array_size(host.DEPTH) - _hex_array_size(len(saved)) - _BITMAP_OVERHEAD
            else:
                mask = None
                if len(saved) != host.DEPTH:
                    raise WireError("full proof must have 256 siblings")
            parsed.append((step["operation"], key, saved, mask))
        # All strings counted above have exactly 64 hex characters. Canonical
        # JSON lets us account for the restored size exactly before expansion.
        # The compact input has its own max_wire_bytes budget: a dense bitmap
        # envelope can be larger than the full representation.
        if restored_size > limits.max_plain_bytes:
            raise WireError("restored full representation size limit")
        steps = []
        for operation, key, saved, mask in parsed:
            if mode == "bitmap":
                siblings, offset = list(host.DEFAULTS[:host.DEPTH]), 0
                for level in range(host.DEPTH):
                    if mask & (1 << level):
                        value = saved[offset]
                        offset += 1
                        if value == host.DEFAULTS[level]:
                            raise WireError("explicit default is not canonical")
                        siblings[level] = value
                siblings = tuple(siblings)
            else:
                siblings = saved
            steps.append(host.Step(operation, key, siblings))
        return host.Batch(previous, next_checkpoint, tuple(steps), signature)
    except WireError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError, zlib.error) as exc:
        raise WireError("invalid transport encoding") from exc


def accept_wire(verifier, wire, mode="full", limits=Limits()):
    batch = decode_batch(wire, mode, limits)
    verifier.accept(batch)
    return batch
