"use client";

export interface FitnessPoint {
  step: number;
  iteration: number | null;
  fitness: number;
  line: number;
}

export interface SundayDeltaPoint {
  sunday: number;
  delta: number;
}

interface FitnessHistoryChartProps {
  points: FitnessPoint[];
}

interface DeltaDistributionChartProps {
  points: SundayDeltaPoint[];
}

const CHART_WIDTH = 640;
const CHART_HEIGHT = 220;
const PADDING = 34;

export function FitnessHistoryChart({ points }: FitnessHistoryChartProps) {
  if (points.length === 0) {
    return <EmptyChart message="No fitness history found in run.log" />;
  }

  const values = points.map((point) => point.fitness);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueSpan = maxValue - minValue || 1;
  const xSpan = Math.max(points.length - 1, 1);

  const xFor = (index: number) =>
    PADDING + (index / xSpan) * (CHART_WIDTH - PADDING * 2);
  const yFor = (value: number) =>
    CHART_HEIGHT - PADDING - ((value - minValue) / valueSpan) * (CHART_HEIGHT - PADDING * 2);

  const path = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xFor(index)} ${yFor(point.fitness)}`)
    .join(" ");

  const sampledPoints = points.filter(
    (_, index) => points.length <= 60 || index % Math.ceil(points.length / 60) === 0,
  );

  return (
    <div>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-56 w-full overflow-visible"
        role="img"
        aria-label="Fitness over optimization progress"
      >
        <line
          x1={PADDING}
          y1={CHART_HEIGHT - PADDING}
          x2={CHART_WIDTH - PADDING}
          y2={CHART_HEIGHT - PADDING}
          stroke="#cbd5e1"
        />
        <line
          x1={PADDING}
          y1={PADDING}
          x2={PADDING}
          y2={CHART_HEIGHT - PADDING}
          stroke="#cbd5e1"
        />
        <path d={path} fill="none" stroke="#2563eb" strokeWidth="2.5" />
        {sampledPoints.map((point) => {
          const index = points.indexOf(point);
          return (
            <circle
              key={`${point.step}-${point.line}`}
              cx={xFor(index)}
              cy={yFor(point.fitness)}
              r="2.5"
              fill="#1d4ed8"
            >
              <title>
                {`Step ${point.step}, iteration ${point.iteration ?? "n/a"}: ${point.fitness.toFixed(3)}`}
              </title>
            </circle>
          );
        })}
        <text x={PADDING} y={20} className="fill-slate-500 text-[11px]">
          {maxValue.toFixed(3)}
        </text>
        <text x={PADDING} y={CHART_HEIGHT - 8} className="fill-slate-500 text-[11px]">
          {minValue.toFixed(3)}
        </text>
        <text x={CHART_WIDTH - PADDING} y={CHART_HEIGHT - 8} textAnchor="end" className="fill-slate-500 text-[11px]">
          {points.length} improvements
        </text>
      </svg>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-600">
        <div>
          <span className="font-medium text-slate-800">First:</span> {points[0].fitness.toFixed(3)}
        </div>
        <div>
          <span className="font-medium text-slate-800">Best:</span> {maxValue.toFixed(3)}
        </div>
        <div>
          <span className="font-medium text-slate-800">Last:</span> {points[points.length - 1].fitness.toFixed(3)}
        </div>
      </div>
    </div>
  );
}

export function DeltaDistributionChart({ points }: DeltaDistributionChartProps) {
  if (points.length === 0) {
    return <EmptyChart message="No Sunday deltas available yet" />;
  }

  const deltas = points.map((point) => point.delta);
  const maxAbsDelta = Math.max(1, ...deltas.map((delta) => Math.abs(delta)));
  const binCount = Math.min(17, Math.max(7, Math.ceil(Math.sqrt(points.length) * 2)));
  const adjustedBinCount = binCount % 2 === 0 ? binCount + 1 : binCount;
  const binWidth = (maxAbsDelta * 2) / adjustedBinCount;
  const bins = Array.from({ length: adjustedBinCount }, (_, index) => {
    const start = -maxAbsDelta + index * binWidth;
    return {
      start,
      end: start + binWidth,
      count: 0,
    };
  });

  deltas.forEach((delta) => {
    const rawIndex = Math.floor((delta + maxAbsDelta) / binWidth);
    const index = Math.min(adjustedBinCount - 1, Math.max(0, rawIndex));
    bins[index].count += 1;
  });

  const maxCount = Math.max(1, ...bins.map((bin) => bin.count));
  const plotWidth = CHART_WIDTH - PADDING * 2;
  const plotHeight = CHART_HEIGHT - PADDING * 2;
  const barGap = 4;
  const barWidth = plotWidth / adjustedBinCount - barGap;
  const zeroX = PADDING + plotWidth / 2;
  const mean = deltas.reduce((sum, delta) => sum + delta, 0) / deltas.length;
  const positiveCount = deltas.filter((delta) => delta > 0).length;
  const negativeCount = deltas.filter((delta) => delta < 0).length;

  return (
    <div>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="h-56 w-full overflow-visible"
        role="img"
        aria-label="Distribution of per-Sunday deltas compared to random"
      >
        <line
          x1={PADDING}
          y1={CHART_HEIGHT - PADDING}
          x2={CHART_WIDTH - PADDING}
          y2={CHART_HEIGHT - PADDING}
          stroke="#cbd5e1"
        />
        <line
          x1={zeroX}
          y1={PADDING - 8}
          x2={zeroX}
          y2={CHART_HEIGHT - PADDING}
          stroke="#334155"
          strokeDasharray="4 4"
        />
        {bins.map((bin, index) => {
          const height = (bin.count / maxCount) * plotHeight;
          const x = PADDING + index * (plotWidth / adjustedBinCount) + barGap / 2;
          const y = CHART_HEIGHT - PADDING - height;
          const midpoint = (bin.start + bin.end) / 2;
          return (
            <rect
              key={`${bin.start}-${bin.end}`}
              x={x}
              y={y}
              width={barWidth}
              height={height}
              rx="3"
              fill={midpoint < 0 ? "#fb7185" : midpoint > 0 ? "#34d399" : "#94a3b8"}
            >
              <title>
                {`${bin.start.toFixed(3)} to ${bin.end.toFixed(3)}: ${bin.count} Sundays`}
              </title>
            </rect>
          );
        })}
        <text x={PADDING} y={CHART_HEIGHT - 8} className="fill-slate-500 text-[11px]">
          {(-maxAbsDelta).toFixed(2)}
        </text>
        <text x={zeroX} y={CHART_HEIGHT - 8} textAnchor="middle" className="fill-slate-700 text-[11px]">
          0
        </text>
        <text x={CHART_WIDTH - PADDING} y={CHART_HEIGHT - 8} textAnchor="end" className="fill-slate-500 text-[11px]">
          {`+${maxAbsDelta.toFixed(2)}`}
        </text>
      </svg>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-600">
        <div>
          <span className="font-medium text-slate-800">Mean:</span> {mean.toFixed(3)}
        </div>
        <div>
          <span className="font-medium text-slate-800">Negative:</span> {negativeCount}
        </div>
        <div>
          <span className="font-medium text-slate-800">Positive:</span> {positiveCount}
        </div>
      </div>
    </div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-40 items-center justify-center rounded border border-dashed border-slate-300 text-sm text-slate-500">
      {message}
    </div>
  );
}
