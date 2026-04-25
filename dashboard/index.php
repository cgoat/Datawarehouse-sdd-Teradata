<?php
// Reliability dashboard — pulls the last 50 pipeline runs from DW_DQ.run_log
// and the latest GE results from DW_DQ.dq_result. Connects to the FastAPI
// helper at api/main.py so we don't need a PHP Teradata driver.

$api = getenv('DW_API') ?: 'http://localhost:8000';

function fetch_json(string $url): array {
  $ctx = stream_context_create(['http' => ['timeout' => 5, 'ignore_errors' => true]]);
  $raw = @file_get_contents($url, false, $ctx);
  if ($raw === false) return ['error' => "cannot reach $url"];
  $decoded = json_decode($raw, true);
  return is_array($decoded) ? $decoded : ['error' => 'bad json'];
}

$runs = fetch_json("$api/runs?limit=50");
$dq   = fetch_json("$api/dq/latest");
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DW Reliability</title>
<style>
 body { font: 14px system-ui, sans-serif; margin: 24px; color: #222; }
 h1 { margin: 0 0 16px; }
 h2 { margin: 24px 0 8px; }
 table { border-collapse: collapse; width: 100%; }
 th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #eee; }
 th { background: #f5f5f5; }
 .ok   { color: #1a7f37; font-weight: 600; }
 .fail { color: #b4252a; font-weight: 600; }
 .started { color: #9a6700; }
 .muted { color: #666; }
 .err { background: #fdecec; padding: 10px; border: 1px solid #f5a5a5; }
</style>
</head>
<body>
<h1>DW Reliability</h1>
<nav style="margin-bottom:16px;">
  <a href="index.php">Reliability</a> &nbsp;|&nbsp;
  <a href="silver.php">Silver</a> &nbsp;|&nbsp;
  <a href="gold.php">Gold</a> &nbsp;|&nbsp;
  <a href="perf.php">Performance</a>
</nav>
<p class="muted">SLA: daily load complete by 07:00. Data pulled from <code><?= htmlspecialchars($api) ?></code>.</p>

<h2>Recent pipeline runs</h2>
<?php if (!empty($runs['error'])): ?>
  <div class="err">API error: <?= htmlspecialchars($runs['error']) ?></div>
<?php else: ?>
<table>
  <tr>
    <th>Batch</th><th>Layer</th><th>Step</th><th>Status</th>
    <th>Tool</th>
    <th>Rows in</th><th>Rows out</th><th>Started</th><th>Duration (s)</th>
  </tr>
  <?php foreach ($runs as $r): ?>
    <tr>
      <td><?= htmlspecialchars($r['batch_id'] ?? '') ?></td>
      <td><?= htmlspecialchars($r['layer'] ?? '') ?></td>
      <td><?= htmlspecialchars($r['step'] ?? '') ?></td>
      <td class="<?= htmlspecialchars($r['status'] ?? '') ?>"><?= htmlspecialchars($r['status'] ?? '') ?></td>
      <td><code><?= htmlspecialchars($r['tool'] ?? '') ?></code></td>
      <td><?= $r['rows_in']  !== null ? number_format((float)$r['rows_in'])  : '' ?></td>
      <td><?= $r['rows_out'] !== null ? number_format((float)$r['rows_out']) : '' ?></td>
      <td><?= htmlspecialchars($r['started_at'] ?? '') ?></td>
      <td><?= htmlspecialchars((string)($r['duration_sec'] ?? '')) ?></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

<h2>Latest DQ results</h2>
<?php if (!empty($dq['error'])): ?>
  <div class="err">API error: <?= htmlspecialchars($dq['error']) ?></div>
<?php else: ?>
<table>
  <tr><th>Table</th><th>Expectation</th><th>Result</th><th>Observed</th><th>Run at</th></tr>
  <?php foreach ($dq as $d): ?>
    <tr>
      <td><?= htmlspecialchars($d['table_name'] ?? '') ?></td>
      <td><?= htmlspecialchars($d['expectation'] ?? '') ?></td>
      <td class="<?= ($d['success'] ?? 0) ? 'ok' : 'fail' ?>">
        <?= ($d['success'] ?? 0) ? 'PASS' : 'FAIL' ?>
      </td>
      <td><?= htmlspecialchars(substr((string)($d['observed_value'] ?? ''), 0, 80)) ?></td>
      <td><?= htmlspecialchars($d['run_at'] ?? '') ?></td>
    </tr>
  <?php endforeach; ?>
</table>
<?php endif; ?>

</body>
</html>
