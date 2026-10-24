"""Public-data state reference, NOT a PSI protocol or a hiding commitment.

SHA-256 sparse tree, 256 levels; Ed25519 from the installed cryptography library.
Keys and paths are public. A trusted initial checkpoint and verification key are
provided out of band. No network parser, durable storage, crash recovery, global
fork prevention, or binding to a separate computation is implemented.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
from itertools import islice
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DEPTH = 256
MAX_STEPS = 4096
DOMAIN = b"ccpe-public-state-reference-v1/"


def _key(key):
    if type(key) is not bytes or len(key) > 4096:
        raise ValueError("key must be bytes of at most 4096 bytes")
    return len(key).to_bytes(8, "big") + key


def _index(key):
    return int.from_bytes(sha256(DOMAIN + b"index/" + _key(key)).digest(), "big")


def _leaf(key):
    return sha256(DOMAIN + b"leaf/" + _key(key)).digest()


def _parent(left, right):
    return sha256(DOMAIN + b"node/" + left + right).digest()


_defaults = [sha256(DOMAIN + b"empty/").digest()]
for _level in range(DEPTH):
    _defaults.append(_parent(_defaults[-1], _defaults[-1]))
DEFAULTS = tuple(_defaults)


class SparseSet:
    """Sparse authenticated set with uncompressed, public 256-sibling paths."""

    def __init__(self, keys=()):
        self._keys = set()
        self._indices = {}
        self._levels = [{} for _ in range(DEPTH + 1)]
        for key in keys:
            _key(key)
            if key not in self._keys:
                self.add(key)

    @property
    def keys(self):
        return frozenset(self._keys)

    def __contains__(self, key):
        return key in self._keys

    def __len__(self):
        return len(self._keys)

    @property
    def root(self):
        return self._levels[DEPTH].get(0, DEFAULTS[DEPTH])

    def proof(self, key):
        index = _index(key)
        siblings = []
        for level in range(DEPTH):
            siblings.append(self._levels[level].get(index ^ 1, DEFAULTS[level]))
            index >>= 1
        return tuple(siblings)

    def _change(self, key, present):
        index = _index(key)
        if present and index in self._indices and self._indices[index] != key:
            raise ValueError("index collision; reference cannot represent both keys")
        value = _leaf(key) if present else DEFAULTS[0]
        updates = [(0, index, value)]
        for level in range(DEPTH):
            sibling = self._levels[level].get(index ^ 1, DEFAULTS[level])
            value = _parent(sibling, value) if index & 1 else _parent(value, sibling)
            index >>= 1
            updates.append((level + 1, index, value))
        for level, position, value in updates:
            if value == DEFAULTS[level]:
                self._levels[level].pop(position, None)
            else:
                self._levels[level][position] = value
        if present:
            self._keys.add(key)
            self._indices[_index(key)] = key
        else:
            self._keys.remove(key)
            self._indices.pop(_index(key))

    def add(self, key):
        _key(key)
        if key in self._keys:
            raise ValueError("duplicate addition")
        self._change(key, True)

    def remove(self, key):
        _key(key)
        if key not in self._keys:
            raise ValueError("removal of absent key")
        self._change(key, False)


def _path_root(key, present, siblings):
    if type(present) is not bool or len(siblings) != DEPTH:
        raise ValueError("invalid path shape")
    index = _index(key)
    value = _leaf(key) if present else DEFAULTS[0]
    for sibling in siblings:
        if type(sibling) is not bytes or len(sibling) != 32:
            raise ValueError("invalid sibling")
        value = _parent(sibling, value) if index & 1 else _parent(value, sibling)
        index >>= 1
    return value


def verify_path(key, present, siblings, root):
    try:
        return type(root) is bytes and len(root) == 32 and _path_root(key, present, siblings) == root
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class Checkpoint:
    session: str
    epoch: int
    root: bytes
    size: int


@dataclass(frozen=True)
class Step:
    operation: str
    key: bytes
    siblings: tuple[bytes, ...]


@dataclass(frozen=True)
class Batch:
    previous: Checkpoint
    next: Checkpoint
    steps: tuple[Step, ...]
    signature: bytes = b""


def _check_checkpoint(checkpoint):
    if not isinstance(checkpoint, Checkpoint):
        raise ValueError("invalid checkpoint type")
    if type(checkpoint.session) is not str or not 1 <= len(checkpoint.session) <= 256:
        raise ValueError("invalid session")
    if type(checkpoint.epoch) is not int or checkpoint.epoch < 0:
        raise ValueError("invalid epoch")
    if type(checkpoint.size) is not int or checkpoint.size < 0:
        raise ValueError("invalid size")
    if type(checkpoint.root) is not bytes or len(checkpoint.root) != 32:
        raise ValueError("invalid root")


def checkpoint_dict(checkpoint):
    return {"session": checkpoint.session, "epoch": checkpoint.epoch,
            "root": checkpoint.root.hex(), "size": checkpoint.size}


def payload(batch):
    body = {"domain": DOMAIN.decode("ascii"),
            "previous": checkpoint_dict(batch.previous), "next": checkpoint_dict(batch.next),
            "steps": [{"operation": step.operation, "key": step.key.hex(),
                       "siblings": [s.hex() for s in step.siblings]} for step in batch.steps]}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def serialized_batch(batch):
    """Export only: JSON with hex encoding, no receiving/network parser provided."""
    body = json.loads(payload(batch))
    body["signature"] = batch.signature.hex()
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("ascii")


class Publisher:
    def __init__(self, keys=(), session="study", signing_key=None):
        self.tree = SparseSet(keys)
        self.signing_key = signing_key or Ed25519PrivateKey.generate()
        self.public_key = self.signing_key.public_key()
        self.checkpoint = Checkpoint(session, 0, self.tree.root, len(self.tree))
        _check_checkpoint(self.checkpoint)

    def apply(self, operations):
        """Sequential batch semantics; validate all operations before mutation.

        Duplicate additions and absent deletions are errors. Remove-then-add is
        legal within a batch. In-memory rollback covers ordinary signing failures;
        this is not a crash-safe transaction or a concurrent API.
        """
        operations = tuple(islice(iter(operations), MAX_STEPS + 1))
        if not 1 <= len(operations) <= MAX_STEPS:
            raise ValueError("batch length out of bounds")
        membership = {}
        for operation, key in operations:
            _key(key)
            present = membership.get(key, key in self.tree)
            if operation not in ("add", "remove") or present != (operation == "remove"):
                raise ValueError("illegal sequential update")
            membership[key] = operation == "add"
        steps, applied = [], []
        try:
            for operation, key in operations:
                steps.append(Step(operation, key, self.tree.proof(key)))
                if operation == "add":
                    self.tree.add(key)
                else:
                    self.tree.remove(key)
                applied.append((operation, key))
            next_checkpoint = Checkpoint(self.checkpoint.session, self.checkpoint.epoch + 1,
                                         self.tree.root, len(self.tree))
            batch = Batch(self.checkpoint, next_checkpoint, tuple(steps))
            batch = replace(batch, signature=self.signing_key.sign(payload(batch)))
        except Exception:
            for operation, key in reversed(applied):
                if operation == "add":
                    self.tree.remove(key)
                else:
                    self.tree.add(key)
            raise
        self.checkpoint = next_checkpoint
        return batch


class Rejected(ValueError):
    pass


class Verifier:
    def __init__(self, public_key, checkpoint):
        _check_checkpoint(checkpoint)
        self.public_key = public_key
        self.checkpoint = checkpoint

    def accept(self, batch):
        """Verify against one locally stored checkpoint, then advance atomically."""
        try:
            if type(batch) is not Batch or type(batch.steps) is not tuple:
                raise Rejected("invalid batch type")
            _check_checkpoint(batch.previous)
            _check_checkpoint(batch.next)
            if not 1 <= len(batch.steps) <= MAX_STEPS:
                raise Rejected("batch length out of bounds")
            if type(batch.signature) is not bytes or len(batch.signature) != 64:
                raise Rejected("invalid signature shape")
            # Bound object fields before serializing them or doing signature work.
            for step in batch.steps:
                if type(step) is not Step or step.operation not in ("add", "remove"):
                    raise Rejected("invalid step")
                _key(step.key)
                if type(step.siblings) is not tuple or len(step.siblings) != DEPTH:
                    raise Rejected("invalid path shape")
                if any(type(s) is not bytes or len(s) != 32 for s in step.siblings):
                    raise Rejected("invalid sibling")
            if batch.previous != self.checkpoint:
                raise Rejected("previous checkpoint mismatch: replay, fork, or wrong session")
            if batch.next.session != self.checkpoint.session or batch.next.epoch != self.checkpoint.epoch + 1:
                raise Rejected("invalid session or epoch transition")
            self.public_key.verify(batch.signature, payload(batch))
            root, size = self.checkpoint.root, self.checkpoint.size
            for step in batch.steps:
                if step.operation not in ("add", "remove"):
                    raise Rejected("unknown operation")
                was_present = step.operation == "remove"
                if not verify_path(step.key, was_present, step.siblings, root):
                    raise Rejected("invalid membership or nonmembership witness")
                root = _path_root(step.key, not was_present, step.siblings)
                size += -1 if was_present else 1
                if size < 0:
                    raise Rejected("negative set size")
            if root != batch.next.root or size != batch.next.size:
                raise Rejected("final root or cardinality mismatch")
        except (InvalidSignature, TypeError, ValueError, AttributeError) as exc:
            raise Rejected(str(exc) or "invalid signature or object") from exc
        self.checkpoint = batch.next
