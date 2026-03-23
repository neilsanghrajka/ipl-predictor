"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import type { TooltipProps, TooltipValueType } from "recharts";

const COLORS = ["#f59e0b", "#6366f1", "#ef4444", "#10b981", "#ec4899", "#06b6d4", "#8b5cf6"];

type TooltipName = number | string;
type TooltipFormatter = NonNullable<TooltipProps<TooltipValueType, TooltipName>["formatter"]>;

function formatPointsValue(value: TooltipValueType | undefined) {
  if (typeof value === "number") {
    return Math.round(value);
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  return 0;
}

const ownerTooltipFormatter: TooltipFormatter = (value, name) => [
  `${formatPointsValue(value)} pts`,
  name === "bat" ? "Batting" : "Bowling",
];

const pieTooltipFormatter: TooltipFormatter = (value) => [`${formatPointsValue(value)} pts`];

const expectedTooltipFormatter: TooltipFormatter = (value) => [`${formatPointsValue(value)} pts`, "Expected"];

const tierTooltipFormatter: TooltipFormatter = (value, _name, item) => {
  const count = "count" in item.payload && typeof item.payload.count === "number" ? item.payload.count : 0;
  return [`${formatPointsValue(value)} pts (${count} players)`];
};

export function OwnerBarChart({ rankings }: { rankings: { name: string; total: number; bat: number; bowl: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={rankings} layout="vertical" margin={{ left: 0, right: 10, top: 5, bottom: 5 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={65} tick={{ fill: "#9ca3af", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "#fff", fontWeight: "bold" }}
          formatter={ownerTooltipFormatter}
        />
        <Bar dataKey="bat" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} name="bat" />
        <Bar dataKey="bowl" stackId="a" fill="#22c55e" radius={[0, 4, 4, 0]} name="bowl" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function BatBowlPie({ bat, bowl }: { bat: number; bowl: number }) {
  const pieData = [
    { name: "Batting", value: Math.round(bat) },
    { name: "Bowling", value: Math.round(bowl) },
  ];
  return (
    <ResponsiveContainer width="100%" height={160}>
      <PieChart>
        <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" stroke="none">
          <Cell fill="#3b82f6" />
          <Cell fill="#22c55e" />
        </Pie>
        <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: "#9ca3af" }} />
        <Tooltip
          contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
          formatter={pieTooltipFormatter}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function PlayerContributionChart({ players }: { players: { fn: string; expTotal: number }[] }) {
  const top10 = [...players].sort((a, b) => b.expTotal - a.expTotal).slice(0, 10);
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={top10} layout="vertical" margin={{ left: 5, right: 10, top: 5, bottom: 5 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="fn"
          width={110}
          tick={{ fill: "#9ca3af", fontSize: 11 }}
          tickFormatter={(v: string) => v.length > 15 ? v.slice(0, 14) + "…" : v}
        />
        <Tooltip
          contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
          formatter={expectedTooltipFormatter}
        />
        <Bar dataKey="expTotal" fill="#f59e0b" radius={[0, 4, 4, 0]}>
          {top10.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TierBreakdownChart({ players }: { players: { tier: string; expTotal: number }[] }) {
  const tierMap: Record<string, { pts: number; count: number }> = {};
  players.forEach((p) => {
    if (!tierMap[p.tier]) tierMap[p.tier] = { pts: 0, count: 0 };
    tierMap[p.tier].pts += p.expTotal;
    tierMap[p.tier].count += 1;
  });
  const tierOrder = ["GUARANTEED", "LIKELY", "ROTATION", "UNLIKELY"];
  const tierLabels: Record<string, string> = { GUARANTEED: "Locked In", LIKELY: "Likely", ROTATION: "Fringe", UNLIKELY: "Bench" };
  const tierColors: Record<string, string> = { GUARANTEED: "#10b981", LIKELY: "#3b82f6", ROTATION: "#eab308", UNLIKELY: "#6b7280" };
  const chartData = tierOrder.map((t) => ({
    name: tierLabels[t] || t,
    pts: Math.round(tierMap[t]?.pts || 0),
    count: tierMap[t]?.count || 0,
    fill: tierColors[t],
  }));

  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={chartData} margin={{ left: 0, right: 10, top: 5, bottom: 5 }}>
        <XAxis dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} />
        <YAxis hide />
        <Tooltip
          contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
          formatter={tierTooltipFormatter}
        />
        <Bar dataKey="pts" radius={[4, 4, 0, 0]}>
          {chartData.map((d, i) => (
            <Cell key={i} fill={d.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
