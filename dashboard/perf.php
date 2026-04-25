<?php
// Performance dashboard — before/after benchmark comparison + raw timings.
$api = getenv('DW_API') ?: 'http://localhost:8000';

function fetch_json(string $url) {
  $ctx = stream_context_create(['http' => ['timeout' => 10, 'ignore_errors' => true]]);
  $raw = @file_get_contents($url, false, $ctx);
  if ($raw === false) return ['error' => "cannot reach $url"];
  $decoded = json_decode($raw, true);
  return is_array($decoded) ? $decoded : ['error' => 'bad json'];
}

$run_id = $_GET['run_id'] ?? '';
$qs = $run_id ? ('?run_id=' . urlencode($run_id)) : '';
$runs    = fetch_json("$api/perf/runs");
$compare = fetch_json("$api/perf/compare$qs");
$raw     = fetch_json("$api/perf/raw$qs");
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DW Performance</title>
<style>
 body { font: 14px system-ui, sans-serif; margin: 24px; color: #222; }
 h1 { margin: 0 0 16px; }
 h2 { margin: 24px 0 8px; }
 nav a { margin-right: 16px; }
 table { border-collapse: collapse; margin-top: 8px; }
 th, td { text-align: left; padding: 6px 12px; border-bottom: 1px solid #eee; }
 th { background: #f5f5f5; }
 td.num { text-align: right; font-variant-numeric: tabular-nums; }
 .ok   { color: #1a7f37; font-weight: 600; }
 .bad  { color: #b4252a; font-weight: 600; }
 .muted { color: #666; }
 .err { background: #fdecec; padding: 10px; border: 1px solid #f5a5a5; }
 .pill { display: inline-block; padding: 2px 8px; border-radius: 10px; background: #eef; margin-right: 4px; font-size: 12px; }
</style>
</head>
<body>
<h1>Performance</h1>
<nav>
  <a href="index.php">Reliability</a>
  <a href="silver.php">Silver</a>
  <a href="gold.php">Gold</a>
  <a href="perf.php">Performance</a>
  <span class="muted">|  Phase 3: benchmark, tune (stats + PPI), re-benchmark</span>
</nav>

<h2>Benchmark runs</h2>
<?php if (!empty($runs['error']) || (count($runs) > 0 && !empty($runs[0]['error']))): ?>
  <div class="err"><?= htmlspecialchars($runs['error'] ?? $runs[0]['error']) ?></div>
<?php elseif (count($runs) === 0): ?>
  <p class="muted">No perf runs yet. Run <code>scripts\run_perf_baseline.bat</code>.</p>
<?php else: ?>
<table>
  <tr><th>Run</th><th>First started</th><th>Phases</th><th>Rows</th><th></th></tr>
  <?php foreach ($runs as $r): ?>
    <tr>
      <td><code><?= htmlspecialchars($r['run_id'] ?? '') ?></code></td>
      <td><?= htmlspecialchars($r['first_at'] ?? '') ?></td>
      <td>
        <?php if (($r['has_before'] ?? 0)): ?><span class="pill">before</span><?php endif; ?>
        <?php if (($r['has_after'] ?? 0)): ?><span class="pill">after</span><?php endif; ?>
      </td>
      <td class="num"><?= number_format((int)($r['row_count'] ?? 0)) ?></td>
      <td><a href="?run_id=<?= urlencode($r['run_id'] ?? '') ?>">view</a></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

<h2>Before vs After (median timings)<?= $run_id ? ' — '.htmlspecialchars($run_id) : '' ?></h2>
<?php if (!empty($compare['error']) || (count($compare) > 0 && !empty($compare[0]['error']))): ?>
  <div class="err"><?= htmlspecialchars($compare['error'] ?? $compare[0]['error']) ?></div>
<?php elseif (count($compare) === 0): ?>
  <p class="muted">No comparison data yet.</p>
<?php else: ?>
<table>
  <tr><th>Query</th><th>Before (s)</th><th>After (s)</th><th>Delta (s)</th><th>Speedup</th></tr>
  <?php foreach ($compare as $r): ?>
    <?php
      $b = $r['before_sec'] ?? null;
      $a = $r['after_sec']  ?? null;
      $d = $r['delta_sec']  ?? null;
      $sp = $r['speedup_x'] ?? null;
      $cls = ($sp !== null && (float)$sp >= 1.10) ? 'ok' : (($sp !== null && (float)$sp < 0.90) ? 'bad' : '');
    ?>
    <tr>
      <td><?= htmlspecialchars($r['query_name'] ?? '') ?></td>
      <td class="num"><?= $b !== null ? number_format((float)$b, 3) : '' ?></td>
      <td class="num"><?= $a !== null ? number_format((float)$a, 3) : '' ?></td>
      <td class="num"><?= $d !== null ? number_format((float)$d, 3) : '' ?></td>
      <td class="num <?= $cls ?>"><?= $sp !== null ? number_format((float)$sp, 2).'x' : '' ?></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

<h2>All iterations<?= $run_id ? ' — '.htmlspecialchars($run_id) : '' ?></h2>
<?php if (!empty($raw['error']) || (count($raw) > 0 && !empty($raw[0]['error']))): ?>
  <div class="err"><?= htmlspecialchars($raw['error'] ?? $raw[0]['error']) ?></div>
<?php else: ?>
<table>
  <tr><th>Query</th><th>Phase</th><th>Iter</th><th>Duration (s)</th><th>Rows</th><th>Started</th></tr>
  <?php foreach ($raw as $r): ?>
    <tr>
      <td><?= htmlspecialchars($r['query_name'] ?? '') ?></td>
      <td><?= htmlspecialchars($r['phase'] ?? '') ?></td>
      <td class="num"><?= htmlspecialchars((string)($r['iteration'] ?? '')) ?></td>
      <td class="num"><?= number_format((float)($r['duration_sec'] ?? 0), 3) ?></td>
      <td class="num"><?= number_format((int)($r['rows_returned'] ?? 0)) ?></td>
      <td><?= htmlspecialchars($r['started_at'] ?? '') ?></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

</body>
</html>
