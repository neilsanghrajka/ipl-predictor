"use client";

import { useState, useMemo } from "react";
import data from "./data.json";
import { OwnerBarChart, BatBowlPie, PlayerContributionChart, TierBreakdownChart } from "./components/charts";
import { DownloadButton, downloadCSV } from "./components/excel-download";

type Player = (typeof data.players)[number];

const TC: Record<string, string> = {
  CSK: "#fbbf24", MI: "#3b82f6", SRH: "#f97316", RCB: "#ef4444",
  PBKS: "#e11d48", RR: "#ec4899", DC: "#6366f1", KKR: "#7c3aed",
  LSG: "#06b6d4", GT: "#14b8a6",
};

const TL: Record<string, { l: string; c: string }> = {
  GUARANTEED: { l: "Locked In", c: "text-emerald-400" },
  LIKELY: { l: "Likely", c: "text-blue-400" },
  ROTATION: { l: "Fringe", c: "text-yellow-400" },
  UNLIKELY: { l: "Bench", c: "text-gray-500" },
};

const RE = ["", "\ud83e\udee1", "\ud83e\udd48", "\ud83e\udd49", "4\ufe0f\u20e3", "5\ufe0f\u20e3", "6\ufe0f\u20e3", "7\ufe0f\u20e3"];

function fmt(n: number) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : Math.round(n).toString(); }

// ─── LEADERBOARD ───
function Leaderboard({ onOwner }: { onOwner: (n: string) => void }) {
  const w = data.rankings[0];
  const mx = w.total;

  return (
    <div className="px-4 pt-6 pb-28">
      <div className="text-center mb-8">
        <div className="text-5xl mb-2">{"\ud83c\udfc6"}</div>
        <h1 className="text-2xl font-bold mb-1">IPL 2026 Fantasy</h1>
        <p className="text-gray-400 text-sm">AI-Powered Predictions &middot; 186 Players &middot; 7 Owners</p>
      </div>

      {/* Winner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-yellow-500/20 via-amber-500/10 to-orange-500/20 border border-yellow-500/30 p-5 mb-6">
        <div className="absolute top-0 right-0 text-8xl opacity-10 -mr-4 -mt-4">{"\ud83c\udfc6"}</div>
        <p className="text-xs uppercase tracking-widest text-yellow-400/80 mb-1">Predicted Winner</p>
        <h2 className="text-3xl font-black">{w.name}</h2>
        <div className="flex flex-wrap gap-3 mt-3 text-sm">
          <span><span className="text-yellow-400 font-bold text-lg">{fmt(w.total)}</span> <span className="text-gray-400">pts</span></span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">{w.count} players</span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">{Math.round((w.bat / w.total) * 100)}% bat / {Math.round((w.bowl / w.total) * 100)}% bowl</span>
        </div>
      </div>

      {/* Stacked bar chart */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-6">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">Points Breakdown</p>
        <div className="flex gap-4 text-xs text-gray-400 mb-2">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-blue-500 inline-block" /> Batting</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-green-500 inline-block" /> Bowling</span>
        </div>
        <OwnerBarChart rankings={data.rankings} />
      </div>

      {/* Rankings */}
      <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">Tap to explore</p>
      <div className="space-y-3">
        {data.rankings.map((o, i) => {
          const pct = (o.total / mx) * 100;
          const gap = i > 0 ? o.total - data.rankings[0].total : 0;
          return (
            <button key={o.name} onClick={() => onOwner(o.name)}
              className="w-full text-left rounded-xl bg-gray-900 border border-gray-800 p-4 hover:border-gray-600 transition-all active:scale-[0.98]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="text-xl w-8 text-center">{RE[o.rank]}</span>
                  <span className="font-bold text-lg">{o.name}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-lg">{fmt(o.total)}</span>
                  <span className="text-gray-500 text-sm ml-1">pts</span>
                  {gap < 0 && <span className="text-red-400/70 text-xs ml-2">{Math.round(gap)}</span>}
                </div>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${pct}%`, background: i === 0 ? "linear-gradient(90deg,#f59e0b,#ef4444)" : "linear-gradient(90deg,#374151,#4b5563)" }} />
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-500">
                <span>{o.count} players</span>
                <span>Bat {fmt(o.bat)} / Bowl {fmt(o.bowl)}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Fun stats */}
      <div className="mt-8 grid grid-cols-2 gap-3">
        {(() => {
          const mvp = [...data.players].sort((a, b) => b.expTotal - a.expTotal)[0];
          const topB = [...data.players].sort((a, b) => b.expBowl - a.expBowl)[0];
          return (
            <>
              <SC l="Most Valuable" v={mvp.fn} s={`${fmt(mvp.expTotal)} pts`} />
              <SC l="Tightest Race" v={`${data.rankings[1].name} vs ${data.rankings[2].name}`} s={`${Math.round(data.rankings[1].total - data.rankings[2].total)} pts gap`} />
              <SC l="Top Bowler" v={topB.fn} s={`${fmt(topB.expBowl)} bowl pts`} />
              <SC l="Injured Stars" v="4 players" s="Hazlewood, Pathirana, Hasaranga, Mayank Y" />
            </>
          );
        })()}
      </div>

      {/* Download */}
      <div className="mt-6">
        <DownloadButton players={data.players} label="Download All Data (CSV)" />
      </div>
    </div>
  );
}

function SC({ l, v, s }: { l: string; v: string; s: string }) {
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-3">
      <p className="text-xs text-gray-500 mb-1">{l}</p>
      <p className="font-bold text-sm truncate">{v}</p>
      <p className="text-xs text-gray-400 mt-0.5">{s}</p>
    </div>
  );
}

// ─── OWNER PROFILE ───
function OwnerProfile({ owner, onBack, onPlayer }: { owner: string; onBack: () => void; onPlayer: (p: Player) => void }) {
  const [sort, setSort] = useState<"points" | "batting" | "bowling">("points");
  const od = data.rankings.find((o) => o.name === owner)!;
  const players = useMemo(
    () => data.players.filter((p) => p.owner === owner).sort((a, b) => sort === "batting" ? b.expBat - a.expBat : sort === "bowling" ? b.expBowl - a.expBowl : b.expTotal - a.expTotal),
    [owner, sort]
  );
  const stars = players.filter((p) => p.tier === "GUARANTEED");
  const teamBreakdown = useMemo(() => {
    const m: Record<string, number> = {};
    players.forEach((p) => { m[p.team] = (m[p.team] || 0) + p.expTotal; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }, [players]);
  const topBat = [...players].sort((a, b) => b.expBat - a.expBat)[0];
  const topBowl = [...players].sort((a, b) => b.expBowl - a.expBowl)[0];
  const overseas = players.filter((p) => p.overseas).length;
  const debs = players.filter((p) => p.debutant).length;
  const hurt = players.filter((p) => p.avail < 1).length;

  return (
    <div className="px-4 pt-4 pb-28">
      <button onClick={onBack} className="text-gray-400 text-sm mb-4 hover:text-white">&larr; Back</button>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-black">{owner}</h2>
          <p className="text-gray-400 text-sm">Rank #{od.rank} of 7</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-black text-yellow-400">{fmt(od.total)}</p>
          <p className="text-xs text-gray-500">predicted pts</p>
        </div>
      </div>

      {/* Text summary */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5 text-sm text-gray-300 leading-relaxed">
        <strong>{owner}</strong>&apos;s squad has <strong>{players.length} players</strong> across {teamBreakdown.length} IPL teams with <strong>{stars.length} guaranteed starters</strong>.
        {topBat && <> Top batter: <strong>{topBat.fn}</strong> ({fmt(topBat.expBat)} pts).</>}
        {topBowl && topBowl.expBowl > 0 && <> Top bowler: <strong>{topBowl.fn}</strong> ({fmt(topBowl.expBowl)} pts).</>}
        {overseas > 0 && <> {overseas} overseas.</>}
        {debs > 0 && <> {debs} debutant{debs > 1 ? "s" : ""}.</>}
        {hurt > 0 && <> {"\u26a0\ufe0f"} {hurt} with availability concerns.</>}
      </div>

      {/* Bat/Bowl pie */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-3">
          <BatBowlPie bat={od.bat} bowl={od.bowl} />
        </div>
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-3">
          <TierBreakdownChart players={players} />
        </div>
      </div>

      {/* Top 10 contributors */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">Top 10 Contributors</p>
        <PlayerContributionChart players={players} />
      </div>

      {/* IPL Teams */}
      <div className="mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Points by IPL Team</p>
        <div className="flex flex-wrap gap-2">
          {teamBreakdown.map(([t, pts]) => (
            <span key={t} className="px-2.5 py-1 rounded-full text-xs font-medium border" style={{ borderColor: TC[t] + "60", color: TC[t] }}>
              {t} {fmt(pts)}
            </span>
          ))}
        </div>
      </div>

      {/* Sort + list */}
      <div className="flex gap-2 mb-3">
        {(["points", "batting", "bowling"] as const).map((s) => (
          <button key={s} onClick={() => setSort(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${sort === s ? "bg-white text-black" : "bg-gray-800 text-gray-400"}`}>
            {s === "points" ? "Total" : s === "batting" ? "Bat" : "Bowl"}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {players.map((p, i) => (
          <button key={p.fn} onClick={() => onPlayer(p)}
            className="w-full text-left rounded-xl bg-gray-900 border border-gray-800 p-3 hover:border-gray-600 transition-all active:scale-[0.98]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs text-gray-600 w-5">{i + 1}</span>
                <span className="w-1.5 h-8 rounded-full flex-shrink-0" style={{ backgroundColor: TC[p.team] }} />
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate">{p.fn}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{p.team}</span>
                    <span>&middot;</span>
                    <span className={TL[p.tier]?.c}>{TL[p.tier]?.l}</span>
                    {p.overseas && <span className="text-orange-400">{"\ud83c\udf0d"}</span>}
                    {p.debutant && <span className="text-purple-400">NEW</span>}
                    {p.avail < 1 && <span className="text-red-400">{"\u26a0\ufe0f"}</span>}
                  </div>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-3">
                <p className="font-bold text-sm">{fmt(p.expTotal)}</p>
                <p className="text-xs text-gray-500">{fmt(p.expBat)}b / {fmt(p.expBowl)}w</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-5">
        <DownloadButton players={players} label={`Download ${owner}'s Squad (CSV)`} filename={`${owner}_squad.csv`} />
      </div>
    </div>
  );
}

// ─── PLAYER DETAIL ───
function PlayerDetail({ player: p, onBack }: { player: Player; onBack: () => void }) {
  const ti = TL[p.tier] || { l: p.tier, c: "text-gray-400" };
  const xiP = p.tier === "GUARANTEED" ? 0.92 : p.tier === "LIKELY" ? 0.75 : p.tier === "ROTATION" ? 0.40 : 0.10;

  return (
    <div className="px-4 pt-4 pb-28">
      <button onClick={onBack} className="text-gray-400 text-sm mb-4 hover:text-white">&larr; Back</button>

      <div className="flex items-start gap-4 mb-6">
        <div className="w-14 h-14 rounded-full flex items-center justify-center text-xl font-black flex-shrink-0" style={{ backgroundColor: TC[p.team] + "30", color: TC[p.team] }}>
          {p.team}
        </div>
        <div>
          <h2 className="text-xl font-black">{p.fn}</h2>
          <div className="flex flex-wrap items-center gap-2 text-sm text-gray-400 mt-1">
            <span>{p.role === "WK" ? "Wicketkeeper" : p.role === "AR" ? "All-Rounder" : p.role === "BOWL" ? "Bowler" : "Batter"}</span>
            <span>&middot;</span><span>{p.team}</span>
            <span>&middot;</span><span>Owned by <strong className="text-white">{p.owner}</strong></span>
            {p.overseas && <><span>&middot;</span><span className="text-orange-400">{"\ud83c\udf0d"} Overseas</span></>}
          </div>
        </div>
      </div>

      {/* Big number */}
      <div className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 p-5 mb-5">
        <div className="text-center mb-4">
          <p className="text-4xl font-black text-yellow-400">{fmt(p.expTotal)}</p>
          <p className="text-xs text-gray-500 mt-1">predicted points</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div><p className="text-lg font-bold text-blue-400">{fmt(p.expBat)}</p><p className="text-xs text-gray-500">batting</p></div>
          <div><p className="text-lg font-bold text-green-400">{fmt(p.expBowl)}</p><p className="text-xs text-gray-500">bowling</p></div>
          <div><p className="text-lg font-bold">{p.expMatches.toFixed(1)}</p><p className="text-xs text-gray-500">matches</p></div>
        </div>
      </div>

      {/* Calculation breakdown */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">{"\ud83e\uddee"} Calculation Breakdown</p>
        <div className="space-y-2 text-sm">
          <R l="Weighted runs/match" v={p.runsPerM.toFixed(1)} />
          <R l="&times; Expected matches" v={p.expMatches.toFixed(1)} />
          <R l="= Batting points" v={fmt(p.expBat)} vc="text-blue-400" />
          <div className="border-t border-gray-800 my-2" />
          <R l="Weighted wickets/match" v={p.wktsPerM.toFixed(2)} />
          <R l="&times; 25 (pts per wicket)" v="25" />
          <R l="&times; Expected matches" v={p.expMatches.toFixed(1)} />
          <R l="= Bowling points" v={fmt(p.expBowl)} vc="text-green-400" />
          <div className="border-t border-gray-800 my-2" />
          <R l="Total expected points" v={fmt(p.expTotal)} vc="text-yellow-400 font-bold" />
        </div>
      </div>

      {/* Match calculation */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">{"\ud83d\udcc5"} Expected Matches</p>
        <div className="space-y-2 text-sm">
          <R l="League matches per team" v="14" />
          <R l={`Playing XI tier`} v={ti.l} vc={ti.c} />
          <R l="Playing XI probability" v={`${Math.round(xiP * 100)}%`} />
          <R l="Availability modifier" v={`${Math.round(p.avail * 100)}%`} vc={p.avail < 1 ? "text-red-400" : ""} />
          <div className="border-t border-gray-800 my-2" />
          <R l="14 &times; XI% &times; Avail%" v={`${p.expMatches.toFixed(1)} matches`} vc="font-bold" />
        </div>
        {p.debutant && <p className="mt-3 text-xs text-purple-400">NEW &mdash; IPL debutant, using fixed baseline estimates</p>}
      </div>

      {/* Availability */}
      {p.availNote && (
        <div className={`rounded-xl border p-4 mb-5 text-sm ${p.avail < 1 ? "bg-red-500/5 border-red-500/20" : "bg-gray-900 border-gray-800"}`}>
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">{p.avail < 1 ? "\u26a0\ufe0f Availability Concern" : "\u2705 Availability"}</p>
          <p className="text-gray-300 leading-relaxed">{p.availNote}</p>
        </div>
      )}

      {/* Career + season stats */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">IPL Career Stats</p>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div><p className="text-2xl font-bold">{p.careerM}</p><p className="text-xs text-gray-500">matches</p></div>
          <div><p className="text-2xl font-bold text-blue-400">{p.careerR.toLocaleString()}</p><p className="text-xs text-gray-500">runs</p></div>
          <div><p className="text-2xl font-bold text-green-400">{p.careerW}</p><p className="text-xs text-gray-500">wickets</p></div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-3">
          <p className="text-xs text-gray-500 mb-2">IPL 2025</p>
          <p className="text-sm"><strong>{p.s25M}</strong> matches</p>
          <p className="text-sm text-blue-400"><strong>{p.s25R}</strong> runs</p>
          <p className="text-sm text-green-400"><strong>{p.s25W}</strong> wickets</p>
        </div>
        <div className="rounded-xl bg-gray-900 border border-gray-800 p-3">
          <p className="text-xs text-gray-500 mb-2">IPL 2024</p>
          <p className="text-sm"><strong>{p.s24M}</strong> matches</p>
          <p className="text-sm text-blue-400"><strong>{p.s24R}</strong> runs</p>
          <p className="text-sm text-green-400"><strong>{p.s24W}</strong> wickets</p>
        </div>
      </div>

      {/* Stat weighting explanation */}
      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4 mb-5">
        <p className="text-xs uppercase tracking-widest text-gray-500 mb-3">{"\u2696\ufe0f"} How Stats Are Weighted</p>
        <div className="space-y-1.5">
          <WB l="IPL 2025" p={50} c="bg-yellow-400" />
          <WB l="IPL 2024" p={30} c="bg-blue-400" />
          <WB l="Career" p={20} c="bg-gray-400" />
        </div>
        <p className="text-xs text-gray-500 mt-3">Recent form matters more &mdash; the 50/30/20 split favors last season while keeping career consistency as an anchor.</p>
      </div>

      <p className="text-xs text-gray-600 text-center">Confidence: {p.conf}</p>
    </div>
  );
}

function R({ l, v, vc = "" }: { l: string; v: string; vc?: string }) {
  return <div className="flex justify-between"><span className="text-gray-400" dangerouslySetInnerHTML={{ __html: l }} /><span className={`font-medium ${vc}`}>{v}</span></div>;
}

function WB({ l, p, c }: { l: string; p: number; c: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-16">{l}</span>
      <div className="flex-1 h-3 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${c}`} style={{ width: `${p}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-8">{p}%</span>
    </div>
  );
}

// ─── ALL PLAYERS ───
function AllPlayers({ onPlayer, onBack }: { onPlayer: (p: Player) => void; onBack: () => void }) {
  const [search, setSearch] = useState("");
  const [ft, setFt] = useState("");

  const list = useMemo(() => {
    let l = [...data.players].sort((a, b) => b.expTotal - a.expTotal);
    if (search) { const q = search.toLowerCase(); l = l.filter((p) => p.fn.toLowerCase().includes(q) || p.n.toLowerCase().includes(q)); }
    if (ft) l = l.filter((p) => p.team === ft);
    return l;
  }, [search, ft]);

  return (
    <div className="px-4 pt-4 pb-28">
      <button onClick={onBack} className="text-gray-400 text-sm mb-4 hover:text-white">&larr; Back</button>
      <h2 className="text-2xl font-black mb-4">All 186 Players</h2>
      <input type="text" placeholder="Search players..." value={search} onChange={(e) => setSearch(e.target.value)}
        className="w-full rounded-xl bg-gray-900 border border-gray-800 px-4 py-3 text-sm mb-3 focus:outline-none focus:border-gray-600" />
      <div className="flex gap-1.5 overflow-x-auto pb-3 mb-3">
        <button onClick={() => setFt("")} className={`px-3 py-1 rounded-full text-xs font-medium flex-shrink-0 ${!ft ? "bg-white text-black" : "bg-gray-800 text-gray-400"}`}>All</button>
        {["CSK","MI","SRH","RCB","PBKS","RR","DC","KKR","LSG","GT"].map((t) => (
          <button key={t} onClick={() => setFt(ft === t ? "" : t)}
            className={`px-3 py-1 rounded-full text-xs font-medium flex-shrink-0 border ${ft === t ? "border-current" : "border-transparent bg-gray-800"}`}
            style={{ color: TC[t] }}>{t}</button>
        ))}
      </div>
      <p className="text-xs text-gray-500 mb-3">{list.length} players</p>
      <div className="space-y-1.5">
        {list.map((p, i) => (
          <button key={p.fn} onClick={() => onPlayer(p)}
            className="w-full text-left flex items-center gap-2 rounded-lg bg-gray-900 border border-gray-800 px-3 py-2 hover:border-gray-600 transition-all">
            <span className="text-xs text-gray-600 w-6">{i + 1}</span>
            <span className="w-1 h-6 rounded-full flex-shrink-0" style={{ backgroundColor: TC[p.team] }} />
            <div className="min-w-0 flex-1">
              <span className="text-sm font-medium truncate block">{p.fn}</span>
              <span className="text-xs text-gray-500">{p.team} &middot; {p.owner}</span>
            </div>
            <span className="font-bold text-sm flex-shrink-0">{fmt(p.expTotal)}</span>
          </button>
        ))}
      </div>
      <div className="mt-5">
        <DownloadButton players={list} label="Download Filtered Data (CSV)" filename="ipl_players_filtered.csv" />
      </div>
    </div>
  );
}

// ─── METHODOLOGY ───
function Methodology({ onBack }: { onBack: () => void }) {
  return (
    <div className="px-4 pt-4 pb-28">
      <button onClick={onBack} className="text-gray-400 text-sm mb-4 hover:text-white">&larr; Back</button>
      <h2 className="text-2xl font-black mb-6">How It Works</h2>
      <MS t="Scoring"><p>Simple: <strong className="text-blue-400">1 run = 1 point</strong>, <strong className="text-green-400">1 wicket = 25 points</strong>. Nothing else counts.</p></MS>
      <MS t="The Formula">
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-sm mb-3"><p>Expected Points =</p><p className="ml-4">Expected Matches &times; (Runs/Match + Wickets/Match &times; 25)</p></div>
        <div className="bg-gray-800 rounded-lg p-3 font-mono text-sm"><p>Expected Matches =</p><p className="ml-4">14 &times; Playing XI % &times; Availability</p></div>
      </MS>
      <MS t="Stat Weighting">
        <p className="mb-2">Recent form is weighted more heavily:</p>
        <WB l="IPL 2025" p={50} c="bg-yellow-400" />
        <WB l="IPL 2024" p={30} c="bg-blue-400" />
        <WB l="Career" p={20} c="bg-gray-400" />
      </MS>
      <MS t="Playing XI Tiers">
        <div className="space-y-2">
          {[
            { t: "Locked In (92%)", d: "Captains, franchise stars. Kohli, Bumrah", c: "text-emerald-400" },
            { t: "Likely (75%)", d: "First-choice, may be rotated. Harshal, Klaasen", c: "text-blue-400" },
            { t: "Fringe (40%)", d: "Competing for spot. Seifert, Shanaka", c: "text-yellow-400" },
            { t: "Bench (10%)", d: "Deep squad, rarely plays", c: "text-gray-500" },
          ].map((x) => <div key={x.t} className="flex gap-3"><span className={`font-bold text-sm w-28 flex-shrink-0 ${x.c}`}>{x.t}</span><span className="text-sm text-gray-400">{x.d}</span></div>)}
        </div>
      </MS>
      <MS t="Availability"><p>Only reduced for player-specific evidence: injury, international duty, retirement. 4 players currently below 100%.</p></MS>
      <MS t="Debutants"><p>16 players with no IPL history get fixed baselines by role.</p></MS>
      <MS t="Overseas Slots"><p>Max 4 overseas per XI. Crowded overseas squads lower fringe overseas players&apos; tier.</p></MS>
      <MS t="Not Modeled"><p>Venue, matchups, toss, position changes, playoffs. Over 14 matches these wash out.</p></MS>
      <MS t="Data Sources"><p>Official IPL stats feeds (iplt20.com), ESPNcricinfo for injuries, LLM-assessed availability to filter real concerns from data artifacts.</p></MS>
    </div>
  );
}

function MS({ t, children }: { t: string; children: React.ReactNode }) {
  return <div className="mb-6"><h3 className="text-sm font-bold uppercase tracking-widest text-gray-400 mb-2">{t}</h3><div className="text-sm text-gray-300 leading-relaxed">{children}</div></div>;
}

// ─── MAIN ───
type View =
  | { p: "home" }
  | { p: "owner"; n: string }
  | { p: "player"; pl: Player; from: string }
  | { p: "method" }
  | { p: "players" };

export default function Home() {
  const [v, setV] = useState<View>({ p: "home" });
  const [tab, setTab] = useState<"home" | "players" | "method">("home");
  const go = (x: View) => { setV(x); window.scrollTo(0, 0); };

  return (
    <div className="max-w-lg mx-auto w-full relative min-h-screen">
      {v.p === "home" && <Leaderboard onOwner={(n) => go({ p: "owner", n })} />}
      {v.p === "owner" && <OwnerProfile owner={v.n} onBack={() => go({ p: "home" })} onPlayer={(pl) => go({ p: "player", pl, from: v.n })} />}
      {v.p === "player" && <PlayerDetail player={v.pl} onBack={() => v.from === "__players" ? (go({ p: "players" }), setTab("players")) : go({ p: "owner", n: v.from })} />}
      {v.p === "method" && <Methodology onBack={() => { go({ p: "home" }); setTab("home"); }} />}
      {v.p === "players" && <AllPlayers onPlayer={(pl) => go({ p: "player", pl, from: "__players" })} onBack={() => { go({ p: "home" }); setTab("home"); }} />}

      <div className="fixed bottom-0 left-0 right-0 bg-gray-950/90 backdrop-blur-xl border-t border-gray-800 z-50">
        <div className="max-w-lg mx-auto flex">
          {([
            { id: "home" as const, ic: "\ud83c\udfc6", lb: "Rankings" },
            { id: "players" as const, ic: "\ud83c\udfcf", lb: "Players" },
            { id: "method" as const, ic: "\ud83e\udde0", lb: "How It Works" },
          ]).map((t) => (
            <button key={t.id} onClick={() => { setTab(t.id); go(t.id === "home" ? { p: "home" } : t.id === "players" ? { p: "players" } : { p: "method" }); }}
              className={`flex-1 py-3 flex flex-col items-center gap-0.5 transition-all ${tab === t.id ? "text-white" : "text-gray-600"}`}>
              <span className="text-lg">{t.ic}</span>
              <span className="text-xs">{t.lb}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
