// Tiny latency chart. One point per check. A failed check (null) is drawn
// as a red tick instead of a point, and the line breaks around it.

type Props = { history: (number | null)[] };

export default function Sparkline({ history }: Props) {
  const W = 300, H = 48, n = history.length;
  if (n < 2) return <svg viewBox={`0 0 ${W} ${H}`} className="spark" />;

  const valid = history.filter((v): v is number => v !== null);
  const max = Math.max(...valid, 1);
  const x = (i: number) => (i / (n - 1)) * W;
  const y = (v: number) => H - 4 - (v / max) * (H - 8);

  let d = "";
  let pen = false;
  const fails: number[] = [];
  history.forEach((v, i) => {
    if (v === null) { pen = false; fails.push(i); return; }
    d += (pen ? " L" : " M") + `${x(i).toFixed(1)},${y(v).toFixed(1)}`;
    pen = true;
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="spark" aria-hidden="true">
      {fails.map((i) => (
        <line key={i} x1={x(i)} y1={4} x2={x(i)} y2={H - 4} className="fail" />
      ))}
      <path d={d} className="line" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
