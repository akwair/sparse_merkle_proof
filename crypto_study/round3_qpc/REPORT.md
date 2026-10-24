# Round3 corrected screening report

## Scope and validity

This report uses only round3_qpc/runs/screening_001 after the real wrapper process exited zero. The original clock-invalid run remains archived separately. No zero sample was dropped or imputed. The corrected run used the identical design with a registered QPC clock amendment.

Rows: 11340; reference 5292, external 6048. Exact frame replay: 252 reference and 288 external frames. Independent Python verification of external proofs: 4752.

本实验为单种子，存在随机噪声风险。Reference domains reuse observed Round2 fixtures; the external domains are fresh but share a generator. Technical repeats are not independent datasets.

## Registered gates

H1 (binary reference): True. H2 (upstream external compact): False. Universal portability gate: False.

| Host | Domain | Cell | Worst byte ratio | Median paired time ratio | Slower pairs / 63 | Pass |
|---|---|---|---:|---:|---:|---|
|external|confirm|n128_q1_absent|1.012500|1.220339|46|False|
|external|confirm|n128_q1_member|1.009868|1.283784|43|False|
|external|confirm|n128_q32_absent|0.990752|1.312972|49|False|
|external|confirm|n128_q32_member|0.938929|1.297513|53|False|
|external|confirm|n2048_q1_absent|1.008621|1.280992|46|False|
|external|confirm|n2048_q1_member|1.008065|1.144068|39|False|
|external|confirm|n2048_q32_absent|0.997695|1.230080|44|False|
|external|confirm|n2048_q32_member|0.946374|1.307310|53|False|
|external|confirm|n512_q1_absent|1.008929|1.250000|48|False|
|external|confirm|n512_q1_member|1.009259|1.233010|45|False|
|external|confirm|n512_q32_absent|0.994056|1.305526|54|False|
|external|confirm|n512_q32_member|0.947552|1.265483|46|False|
|external|dev|n128_q1_absent|1.008902|1.188235|41|False|
|external|dev|n128_q1_member|1.010000|1.276119|48|False|
|external|dev|n128_q32_absent|0.981620|1.347469|54|False|
|external|dev|n128_q32_member|0.903316|1.233333|50|False|
|external|dev|n2048_q1_absent|1.010000|1.300000|50|False|
|external|dev|n2048_q1_member|1.009259|1.362245|50|False|
|external|dev|n2048_q32_absent|0.993164|1.283974|44|False|
|external|dev|n2048_q32_member|0.954434|1.215548|45|False|
|external|dev|n512_q1_absent|1.010000|1.333333|45|False|
|external|dev|n512_q1_member|1.010000|1.281553|47|False|
|external|dev|n512_q32_absent|0.990759|1.253650|50|False|
|external|dev|n512_q32_member|0.942928|1.265557|53|False|
|reference|confirm|n128_k1|0.051752|0.902230|19|True|
|reference|confirm|n128_k16|0.035993|0.965101|23|True|
|reference|confirm|n2048_k1|0.065328|0.969648|22|True|
|reference|confirm|n2048_k16|0.051211|0.959051|23|True|
|reference|confirm|n512_k1|0.057522|0.956707|19|True|
|reference|confirm|n512_k16|0.044024|0.973162|23|True|
|reference|dev|n128_k1|0.047447|0.952392|23|True|
|reference|dev|n128_k16|0.036937|0.965896|23|True|
|reference|dev|n2048_k1|0.062955|0.934016|25|True|
|reference|dev|n2048_k16|0.050817|0.972166|26|True|
|reference|dev|n512_k1|0.055145|0.931842|21|True|
|reference|dev|n512_k16|0.044238|0.952562|23|True|

## Structural diagnosis

All exact byte identities matched archived frames. For the reference, binary omission saves 32(255-k) bytes per step; for the external wrapper it saves 32(d-k)-2-ceil(d/8). The latter includes a two-byte original-depth field. These identities hold for our documented envelopes, not every possible serialization.

{
  "depth_range": [
    5,
    21
  ],
  "proofs": 1188,
  "placeholders": 780,
  "no_placeholder_proofs": 778,
  "compact_larger_bundles": 28,
  "compact_smaller_bundles": 44
}

A compact frame that adds mask/depth metadata but omits too few placeholder nodes can become larger. This accounting directly diagnoses the byte outcome. Timing ratios include compaction, encoding, reconstruction and unchanged verification; exact cache, allocation and scheduler causes have not been isolated. Do not label timing differences as cryptographic degradation.

## Decision

If either gate fails, do not claim host-independent bitmap dominance. The proposed universal-dominance premise is rejected within the measured conditions; no selector or network advantage is asserted. Retain the negative result and revise the manuscript around baseline sensitivity. A new adaptive or concurrency study requires a separate specific hypothesis, prior-art review and PLAN.

## Full mode metrics

|Host/domain/cell|Mode|Median bytes|Median total (ms)|p95 total (ms)|Max total (ms)|Encode median (ms)|Decode median (ms)|Verify median (ms)|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|external/confirm/n128_q1_absent|ordinary|337|0.006800|0.056910|0.148300|0.002300|0.001100|0.003900|
|external/confirm/n128_q1_absent|zlib-compact|353|0.204600|1.017950|2.530700|0.172600|0.010700|0.004900|
|external/confirm/n128_q1_absent|zlib-ordinary|350|0.311700|0.695580|2.168700|0.263400|0.011900|0.006100|
|external/confirm/n128_q1_absent|compact|340|0.009200|0.040270|0.230100|0.003800|0.001600|0.003800|
|external/confirm/n128_q1_member|compact|339|0.010600|0.021240|0.238000|0.004100|0.002000|0.004300|
|external/confirm/n128_q1_member|zlib-compact|352|0.199500|0.935540|1.078700|0.179400|0.013400|0.005900|
|external/confirm/n128_q1_member|zlib-ordinary|349|0.217500|0.734380|1.218600|0.184800|0.014200|0.007000|
|external/confirm/n128_q1_member|ordinary|336|0.007800|0.020200|0.127600|0.002300|0.001000|0.004300|
|external/confirm/n128_q32_absent|zlib-compact|5555|1.008400|2.651710|16.476000|0.516800|0.159800|0.126600|
|external/confirm/n128_q32_absent|ordinary|9883|0.173300|0.671410|0.939600|0.024300|0.018700|0.122100|
|external/confirm/n128_q32_absent|compact|9533|0.237800|0.681470|1.179100|0.060800|0.030600|0.135200|
|external/confirm/n128_q32_absent|zlib-ordinary|5434|1.044600|2.271910|6.042000|0.610800|0.148100|0.129600|
|external/confirm/n128_q32_member|ordinary|10758|0.195700|0.485680|0.661200|0.023700|0.018800|0.144800|
|external/confirm/n128_q32_member|zlib-compact|6006|1.082500|1.901140|3.225900|0.592400|0.167200|0.156100|
|external/confirm/n128_q32_member|zlib-ordinary|5979|0.992600|1.495290|2.075300|0.457800|0.152300|0.148300|
|external/confirm/n128_q32_member|compact|10032|0.248300|0.865440|1.214800|0.058900|0.029800|0.148100|
|external/confirm/n2048_q1_absent|ordinary|497|0.012600|0.035240|0.345800|0.002900|0.001400|0.007200|
|external/confirm/n2048_q1_absent|compact|469|0.014500|0.044530|0.089900|0.005300|0.002100|0.006900|
|external/confirm/n2048_q1_absent|zlib-ordinary|510|0.299500|2.244250|4.437500|0.280500|0.013300|0.009100|
|external/confirm/n2048_q1_absent|zlib-compact|482|0.455300|2.493530|5.537100|0.424800|0.020500|0.009600|
|external/confirm/n2048_q1_member|zlib-compact|513|0.318600|1.674680|3.798500|0.282200|0.016300|0.011600|
|external/confirm/n2048_q1_member|zlib-ordinary|509|0.567600|2.314890|6.739600|0.513800|0.029300|0.011900|
|external/confirm/n2048_q1_member|ordinary|496|0.018800|0.046930|0.262200|0.004100|0.002000|0.011000|
|external/confirm/n2048_q1_member|compact|500|0.019500|0.195610|2.586400|0.006500|0.002700|0.009000|
|external/confirm/n2048_q32_absent|zlib-compact|9867|1.579100|2.682560|9.304400|0.853100|0.261200|0.201600|
|external/confirm/n2048_q32_absent|ordinary|13885|0.300300|0.857980|1.697300|0.031600|0.024500|0.219500|
|external/confirm/n2048_q32_absent|zlib-ordinary|9960|1.433400|2.752850|5.248600|0.803100|0.242000|0.199500|
|external/confirm/n2048_q32_absent|compact|13853|0.342600|0.914260|1.045500|0.090000|0.038000|0.194500|
|external/confirm/n2048_q32_member|zlib-compact|10092|1.519900|3.399520|5.253900|0.809900|0.252900|0.245700|
|external/confirm/n2048_q32_member|compact|14280|0.358900|0.804880|1.294400|0.084000|0.039300|0.223100|
|external/confirm/n2048_q32_member|zlib-ordinary|10113|1.528900|2.820250|9.812400|0.895300|0.242000|0.233300|
|external/confirm/n2048_q32_member|ordinary|15302|0.273400|0.706580|1.290700|0.028000|0.023300|0.216700|
|external/confirm/n512_q1_absent|zlib-compact|352|0.324400|0.793060|1.087000|0.256600|0.021800|0.005900|
|external/confirm/n512_q1_absent|ordinary|336|0.007400|0.017500|0.191700|0.002000|0.001000|0.004300|
|external/confirm/n512_q1_absent|zlib-ordinary|349|0.225700|0.811980|1.014100|0.197900|0.013100|0.006400|
|external/confirm/n512_q1_absent|compact|339|0.009500|0.017800|0.020800|0.003600|0.001600|0.004300|
|external/confirm/n512_q1_member|compact|436|0.012900|0.042150|0.109200|0.004200|0.001800|0.005900|
|external/confirm/n512_q1_member|ordinary|432|0.010300|0.034360|0.444500|0.002600|0.001300|0.006200|
|external/confirm/n512_q1_member|zlib-ordinary|445|0.261100|0.878680|1.957400|0.230900|0.015000|0.008200|
|external/confirm/n512_q1_member|zlib-compact|449|0.289200|0.910700|2.634300|0.222100|0.014400|0.008100|
|external/confirm/n512_q32_absent|zlib-compact|7737|1.656700|2.448280|5.200400|1.086400|0.255800|0.167200|
|external/confirm/n512_q32_absent|zlib-ordinary|7756|1.559100|2.963580|4.388200|1.052500|0.228500|0.180000|
|external/confirm/n512_q32_absent|compact|11826|0.290200|0.708660|1.130300|0.071800|0.034800|0.166900|
|external/confirm/n512_q32_absent|ordinary|12060|0.218300|0.737390|2.539600|0.025700|0.021100|0.164100|
|external/confirm/n512_q32_member|ordinary|12902|0.245900|1.538500|4.442900|0.031600|0.023800|0.182100|
|external/confirm/n512_q32_member|zlib-compact|8001|1.466600|2.865430|6.580900|0.969100|0.221200|0.185000|
|external/confirm/n512_q32_member|zlib-ordinary|8053|1.458300|2.596010|3.843700|0.920500|0.206700|0.199100|
|external/confirm/n512_q32_member|compact|12032|0.314300|0.789700|1.739100|0.085000|0.046600|0.182600|
|external/dev/n128_q1_absent|compact|340|0.009500|0.099350|0.263000|0.003800|0.001700|0.004000|
|external/dev/n128_q1_absent|zlib-ordinary|350|0.218500|0.937890|2.113300|0.195200|0.011600|0.006200|
|external/dev/n128_q1_absent|ordinary|337|0.008600|0.061750|0.170800|0.002600|0.001400|0.004500|
|external/dev/n128_q1_absent|zlib-compact|353|0.164200|0.537110|0.884900|0.129900|0.012600|0.005500|
|external/dev/n128_q1_member|zlib-ordinary|413|0.198300|0.714870|0.782300|0.176800|0.018700|0.006900|
|external/dev/n128_q1_member|zlib-compact|417|0.225500|0.612760|2.314400|0.192300|0.013600|0.007200|
|external/dev/n128_q1_member|ordinary|400|0.008700|0.059480|0.151800|0.002100|0.001100|0.005100|
|external/dev/n128_q1_member|compact|404|0.011500|0.019580|0.090100|0.004000|0.001700|0.005100|
|external/dev/n128_q32_absent|ordinary|9914|0.149400|0.351660|1.014000|0.020700|0.016600|0.111200|
|external/dev/n128_q32_absent|compact|9631|0.198300|0.623470|1.101100|0.054000|0.027400|0.114400|
|external/dev/n128_q32_absent|zlib-compact|5806|0.942600|2.416030|3.021800|0.522000|0.151200|0.120100|
|external/dev/n128_q32_absent|zlib-ordinary|5719|0.893800|2.533730|3.610200|0.505500|0.139100|0.118900|
|external/dev/n128_q32_member|zlib-ordinary|6186|0.762300|1.780290|3.184900|0.397700|0.141800|0.153200|
|external/dev/n128_q32_member|zlib-compact|6314|0.859300|1.625910|2.393800|0.448100|0.156400|0.150800|
|external/dev/n128_q32_member|compact|10136|0.251500|0.654720|0.810000|0.057700|0.029600|0.147000|
|external/dev/n128_q32_member|ordinary|11398|0.192900|0.615200|0.758300|0.022100|0.018300|0.151100|
|external/dev/n2048_q1_absent|ordinary|432|0.009000|0.018700|0.025600|0.001800|0.001100|0.005600|
|external/dev/n2048_q1_absent|compact|436|0.012100|0.021770|0.100700|0.004300|0.001800|0.005800|
|external/dev/n2048_q1_absent|zlib-ordinary|445|0.228000|0.718450|1.083800|0.158100|0.012500|0.007600|
|external/dev/n2048_q1_absent|zlib-compact|449|0.316600|0.693620|1.100600|0.272900|0.016600|0.007500|
|external/dev/n2048_q1_member|zlib-compact|481|0.286000|0.810990|1.031200|0.235000|0.016200|0.008100|
|external/dev/n2048_q1_member|ordinary|464|0.010000|0.020250|0.069700|0.002200|0.001100|0.006500|
|external/dev/n2048_q1_member|zlib-ordinary|477|0.183600|0.821700|0.950700|0.119700|0.012600|0.008000|
|external/dev/n2048_q1_member|compact|468|0.013200|0.066520|0.238400|0.004600|0.002000|0.006300|
|external/dev/n2048_q32_absent|compact|13985|0.289000|0.780110|1.840000|0.073700|0.034900|0.168700|
|external/dev/n2048_q32_absent|ordinary|14145|0.217700|0.770600|1.021000|0.024000|0.021200|0.170100|
|external/dev/n2048_q32_absent|zlib-compact|10112|1.277400|1.920070|7.070100|0.747900|0.221900|0.180800|
|external/dev/n2048_q32_absent|zlib-ordinary|10033|1.323200|2.781590|3.523600|0.778200|0.213700|0.180100|
|external/dev/n2048_q32_member|compact|14055|0.320400|0.767310|1.189600|0.076100|0.035000|0.200400|
|external/dev/n2048_q32_member|ordinary|14918|0.251400|0.771410|1.264800|0.026900|0.022500|0.194800|
|external/dev/n2048_q32_member|zlib-compact|9811|1.398700|2.124050|4.370300|0.665300|0.235100|0.219900|
|external/dev/n2048_q32_member|zlib-ordinary|10267|1.356500|2.193020|3.397200|0.686600|0.224400|0.213000|
|external/dev/n512_q1_absent|ordinary|400|0.008000|0.110170|0.171700|0.002200|0.001100|0.004600|
|external/dev/n512_q1_absent|zlib-ordinary|413|0.201000|0.482440|0.716100|0.154900|0.009800|0.005800|
|external/dev/n512_q1_absent|compact|404|0.010100|0.078590|0.355800|0.003900|0.001900|0.004400|
|external/dev/n512_q1_absent|zlib-compact|417|0.226000|0.521380|0.982100|0.185000|0.012400|0.006700|
|external/dev/n512_q1_member|compact|404|0.011300|0.050860|0.113400|0.004000|0.001800|0.005600|
|external/dev/n512_q1_member|ordinary|400|0.009300|0.016230|0.046100|0.002300|0.001200|0.005600|
|external/dev/n512_q1_member|zlib-ordinary|413|0.167500|0.719350|2.405000|0.128500|0.026100|0.007000|
|external/dev/n512_q1_member|zlib-compact|417|0.356600|0.632150|9.420200|0.214500|0.025900|0.007300|
|external/dev/n512_q32_absent|compact|11823|0.238800|0.758990|1.048500|0.057700|0.028300|0.132000|
|external/dev/n512_q32_absent|ordinary|11935|0.179300|0.598090|14.014300|0.023300|0.018600|0.132700|
|external/dev/n512_q32_absent|zlib-ordinary|7906|0.894100|1.350850|1.492900|0.413900|0.159300|0.128800|
|external/dev/n512_q32_absent|zlib-compact|7991|0.972900|1.734560|2.354400|0.447500|0.178800|0.135600|
|external/dev/n512_q32_member|ordinary|12966|0.203600|0.634870|0.914200|0.021800|0.019800|0.157700|
|external/dev/n512_q32_member|zlib-ordinary|8055|1.082100|1.631100|2.669800|0.499400|0.166000|0.161900|
|external/dev/n512_q32_member|zlib-compact|8137|1.219900|1.642560|2.126800|0.712100|0.180400|0.157700|
|external/dev/n512_q32_member|compact|12226|0.262200|0.727640|0.787200|0.062000|0.032100|0.152700|
|reference/confirm/n128_k1|binary-zlib|8810|3.033400|3.784790|3.983000|0.399000|0.359100|2.129300|
|reference/confirm/n128_k1|binary-full|16637|2.662100|3.356980|3.466300|0.090200|0.319800|2.231400|
|reference/confirm/n128_k1|binary-bitmap|829|2.298700|3.136500|3.512700|0.118700|0.152800|2.015300|
|reference/confirm/n128_k1|zlib|10850|4.988300|6.356480|6.570700|1.310300|1.457700|2.222700|
|reference/confirm/n128_k1|full|34934|4.169200|5.246270|5.408300|0.490300|1.384200|2.259700|
|reference/confirm/n128_k1|bitmap|1889|2.931500|3.995270|4.088500|0.642000|0.228700|2.045900|
|reference/confirm/n128_k1|binary-bitmap-zlib|774|2.361600|3.289580|3.419200|0.193700|0.174400|1.995700|
|reference/confirm/n128_k16|zlib|25379|69.608200|80.838710|94.009600|13.677400|22.397000|34.063800|
|reference/confirm/n128_k16|full|551761|62.651900|73.275410|91.077000|7.489700|22.196500|33.611400|
|reference/confirm/n128_k16|binary-bitmap|9337|37.707700|44.340500|49.523100|1.861800|1.824600|34.109100|
|reference/confirm/n128_k16|bitmap|21042|45.692900|54.319710|56.202100|9.835200|2.511300|33.231900|
|reference/confirm/n128_k16|binary-zlib|17801|42.271600|50.684530|51.202200|3.875800|4.744500|34.174100|
|reference/confirm/n128_k16|binary-bitmap-zlib|6497|38.436100|44.427770|45.479000|2.055300|1.841500|34.710300|
|reference/confirm/n128_k16|binary-full|262969|39.340600|45.744650|50.728900|1.266100|4.417900|34.000100|
|reference/confirm/n2048_k1|zlib|11045|5.029300|6.160360|6.295500|1.316400|1.531700|2.186500|
|reference/confirm/n2048_k1|binary-bitmap|1087|2.383300|3.108830|3.374900|0.122900|0.153800|2.073100|
|reference/confirm/n2048_k1|full|34938|4.021700|4.925710|5.262700|0.463800|1.265400|2.188600|
|reference/confirm/n2048_k1|bitmap|2429|2.835800|3.803840|4.056700|0.651600|0.231200|1.978300|
|reference/confirm/n2048_k1|binary-zlib|8969|2.858300|3.776650|4.496800|0.388300|0.364900|2.086200|
|reference/confirm/n2048_k1|binary-full|16639|2.585200|3.248150|3.878900|0.081000|0.301000|2.198500|
|reference/confirm/n2048_k1|binary-bitmap-zlib|1047|2.511000|3.260340|3.621800|0.200600|0.185300|2.084100|
|reference/confirm/n2048_k16|full|551765|62.253000|96.348410|101.301200|7.897500|21.165200|33.776000|
|reference/confirm/n2048_k16|binary-bitmap|13403|39.291800|57.447290|63.575800|2.017300|2.034800|35.706800|
|reference/confirm/n2048_k16|binary-full|262971|41.517000|59.753530|65.671900|1.385400|4.846500|35.000400|
|reference/confirm/n2048_k16|binary-bitmap-zlib|10117|38.703000|53.949880|64.371900|2.364300|2.068500|34.081200|
|reference/confirm/n2048_k16|bitmap|29555|47.101500|66.482050|80.635800|10.206100|3.012200|34.641700|
|reference/confirm/n2048_k16|zlib|29830|70.403700|101.155930|110.055600|13.969500|22.095000|34.738600|
|reference/confirm/n2048_k16|binary-zlib|21427|43.276800|66.977640|71.201400|4.324100|4.844300|34.881500|
|reference/confirm/n512_k1|binary-bitmap-zlib|846|2.537400|3.353010|3.401000|0.203900|0.189400|2.175900|
|reference/confirm/n512_k1|zlib|10902|5.044800|6.171180|6.646500|1.345600|1.500700|2.199400|
|reference/confirm/n512_k1|full|34934|4.155300|5.399890|5.622400|0.470000|1.367200|2.221600|
|reference/confirm/n512_k1|binary-full|16637|2.666300|3.390470|3.461100|0.083500|0.323900|2.271800|
|reference/confirm/n512_k1|binary-zlib|8848|2.939500|3.911040|4.138400|0.396800|0.356200|2.223200|
|reference/confirm/n512_k1|bitmap|2157|3.061600|4.040080|4.306000|0.655400|0.240700|2.123900|
|reference/confirm/n512_k1|binary-bitmap|957|2.501400|3.206990|3.384300|0.130000|0.166200|2.183400|
|reference/confirm/n512_k16|binary-bitmap-zlib|8551|36.047800|42.289900|45.485800|2.176400|1.813700|31.923200|
|reference/confirm/n512_k16|binary-full|262969|37.035200|44.757020|45.958100|1.125700|4.257800|31.594500|
|reference/confirm/n512_k16|binary-zlib|19910|40.382600|47.994600|52.746100|3.817400|4.488900|32.648900|
|reference/confirm/n512_k16|full|551761|59.882600|72.384490|76.881200|7.156400|20.529900|31.700800|
|reference/confirm/n512_k16|binary-bitmap|11481|35.669700|42.211570|44.177600|1.859600|1.778100|31.460900|
|reference/confirm/n512_k16|bitmap|25531|45.192600|52.209230|54.971400|9.585800|2.745000|32.908500|
|reference/confirm/n512_k16|zlib|28324|65.527800|77.078250|88.439200|13.109400|21.841500|31.613800|
|reference/dev/n128_k1|binary-zlib|8805|2.310000|3.697780|3.981500|0.334100|0.289100|1.588000|
|reference/dev/n128_k1|binary-bitmap|757|1.788200|2.688620|2.880600|0.098100|0.119300|1.531800|
|reference/dev/n128_k1|binary-bitmap-zlib|702|1.849500|3.013080|3.334900|0.162200|0.136800|1.534100|
|reference/dev/n128_k1|zlib|10844|3.951800|5.649950|6.151800|1.080800|1.208600|1.569800|
|reference/dev/n128_k1|bitmap|1747|2.275000|3.591230|4.404100|0.509800|0.175100|1.548600|
|reference/dev/n128_k1|binary-full|16629|1.843900|3.356600|4.614500|0.065800|0.219100|1.525400|
|reference/dev/n128_k1|full|34926|2.982000|5.098310|5.773500|0.375500|0.998500|1.502000|
|reference/dev/n128_k16|binary-bitmap|9553|34.719800|42.895730|47.120000|1.814800|1.609300|31.653400|
|reference/dev/n128_k16|zlib|25737|66.286300|76.084220|84.862600|13.282500|21.634900|31.485200|
|reference/dev/n128_k16|binary-zlib|17925|40.811700|49.285090|50.792700|3.775800|4.636400|31.492500|
|reference/dev/n128_k16|bitmap|21503|44.109500|51.383680|54.116500|9.690600|2.355400|32.069000|
|reference/dev/n128_k16|full|551753|59.194000|69.442770|75.490500|7.045600|20.935500|30.893600|
|reference/dev/n128_k16|binary-bitmap-zlib|6421|36.116800|41.978790|46.163000|2.091400|1.793700|32.371900|
|reference/dev/n128_k16|binary-full|262961|36.271900|45.108880|47.093100|1.211300|4.059500|31.145200|
|reference/dev/n2048_k1|binary-zlib|8930|2.701600|3.886310|4.151900|0.389400|0.337600|1.957900|
|reference/dev/n2048_k1|bitmap|2287|2.950000|3.944210|4.528600|0.621800|0.236500|2.071300|
|reference/dev/n2048_k1|binary-full|16631|2.411100|3.347870|3.965900|0.089300|0.291300|2.024400|
|reference/dev/n2048_k1|zlib|11002|4.815100|6.324800|6.569000|1.356500|1.453000|2.070500|
|reference/dev/n2048_k1|binary-bitmap|1015|2.354400|3.021040|3.132300|0.126700|0.153900|2.067900|
|reference/dev/n2048_k1|full|34930|4.021300|4.982380|5.628600|0.467500|1.339200|2.111300|
|reference/dev/n2048_k1|binary-bitmap-zlib|975|2.433600|3.262760|3.418900|0.195200|0.169500|2.026400|
|reference/dev/n2048_k16|binary-zlib|21608|39.549200|48.009180|50.321000|3.745200|4.458100|31.134800|
|reference/dev/n2048_k16|binary-bitmap|13331|34.943600|43.328070|44.835700|1.869300|1.789900|31.424900|
|reference/dev/n2048_k16|binary-bitmap-zlib|10108|36.127900|43.525070|45.709300|2.191500|1.812500|32.620700|
|reference/dev/n2048_k16|full|551757|60.452700|71.226400|85.640700|7.300500|20.271200|32.600500|
|reference/dev/n2048_k16|bitmap|29413|43.710800|52.673080|59.551200|9.392400|2.653700|32.030800|
|reference/dev/n2048_k16|zlib|30174|66.414100|79.003930|84.386200|13.383900|21.479900|31.115900|
|reference/dev/n2048_k16|binary-full|262963|36.663100|44.735830|47.258800|1.164100|4.159600|31.207400|
|reference/dev/n512_k1|binary-full|16629|2.878200|3.468930|3.807000|0.102500|0.352300|2.395700|
|reference/dev/n512_k1|zlib|10920|5.490500|6.549590|8.199600|1.461800|1.705900|2.336400|
|reference/dev/n512_k1|full|34926|4.445600|5.492300|7.846400|0.547300|1.441400|2.342100|
|reference/dev/n512_k1|binary-zlib|8864|3.502300|4.044440|5.611000|0.457600|0.455000|2.567500|
|reference/dev/n512_k1|binary-bitmap|885|2.671200|3.378650|4.297200|0.137300|0.172600|2.372000|
|reference/dev/n512_k1|binary-bitmap-zlib|838|2.712600|3.403340|4.653900|0.215000|0.196000|2.327600|
|reference/dev/n512_k1|bitmap|2015|3.394000|4.129210|5.332800|0.785000|0.271000|2.313000|
|reference/dev/n512_k16|full|551753|66.075400|95.792210|103.615000|7.845200|22.642300|35.517900|
|reference/dev/n512_k16|binary-zlib|19762|44.204400|61.799770|82.240800|4.255200|4.854900|35.422500|
|reference/dev/n512_k16|binary-bitmap-zlib|8365|39.905000|59.396940|66.524800|2.309700|2.001400|35.649700|
|reference/dev/n512_k16|binary-bitmap|11505|38.999100|53.803520|63.906500|1.990800|1.945800|34.922700|
|reference/dev/n512_k16|binary-full|262961|41.783800|56.329020|66.999900|1.370500|4.689000|35.577000|
|reference/dev/n512_k16|zlib|28117|71.765000|103.212760|107.474000|14.457300|23.526600|34.068100|
|reference/dev/n512_k16|bitmap|25590|48.219100|70.907600|90.657500|10.484500|2.864900|36.015400|
