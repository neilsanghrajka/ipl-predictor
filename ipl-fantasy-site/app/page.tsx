"use client";

import { useState, useMemo, useCallback } from "react";
import data from "./data.json";
import { downloadCSV } from "./components/excel-download";

type Player = (typeof data.players)[number];

/* ── Constants ── */
const TEAM_C: Record<string, string> = {
  CSK: "#D4A017", MI: "#004BA0", SRH: "#FF822A", RCB: "#D4213D",
  PBKS: "#DD1F2D", RR: "#EA1A85", DC: "#4B64E8", KKR: "#3A225D",
  LSG: "#005DA0", GT: "#1B2133",
};
const OWNER_C = ["#D97706", "#7C3AED", "#059669", "#DC2626", "#2563EB", "#DB2777", "#0891B2"];
const TIER: Record<string, { label: string; color: string; bg: string; prob: number }> = {
  GUARANTEED: { label: "Locked In", color: "#059669", bg: "#ECFDF5", prob: 92 },
  LIKELY: { label: "Likely", color: "#2563EB", bg: "#EFF6FF", prob: 75 },
  ROTATION: { label: "Fringe", color: "#D97706", bg: "#FFFBEB", prob: 40 },
  UNLIKELY: { label: "Bench", color: "#9CA3AF", bg: "#F3F4F6", prob: 10 },
};
const ROLE: Record<string, string> = { WK: "Wicketkeeper", AR: "All-Rounder", BOWL: "Bowler", BAT: "Batter" };

function fmt(n: number) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : Math.round(n).toString(); }

/* ── Navigation ── */
type View = { type: "home" } | { type: "owner"; name: string } | { type: "player"; player: Player } | { type: "method" } | { type: "allPlayers" };

export default function Home() {
  const [stack, setStack] = useState<View[]>([{ type: "home" }]);
  const view = stack[stack.length - 1];

  const push = useCallback((v: View) => {
    setStack(s => [...s, v]);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);
  const pop = useCallback(() => {
    setStack(s => s.length > 1 ? s.slice(0, -1) : s);
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  return (
    <div className="max-w-md mx-auto w-full min-h-dvh">
      {view.type === "home" && <HomeScreen push={push} />}
      {view.type === "owner" && <OwnerScreen name={view.name} pop={pop} push={push} />}
      {view.type === "player" && <PlayerScreen player={view.player} pop={pop} />}
      {view.type === "method" && <MethodScreen pop={pop} />}
      {view.type === "allPlayers" && <AllPlayersScreen pop={pop} push={push} />}
    </div>
  );
}

/* ═══════════════════════════
   HOME
   ═══════════════════════════ */
function HomeScreen({ push }: { push: (v: View) => void }) {
  const w = data.rankings[0];
  return (
    <div className="px-5 pt-8 pb-10 fade-up">
      <div className="text-center mb-8">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-medium" style={{ background: "#FEF3C7", color: "#92400E" }}>
          AI-Powered Predictions
        </span>
        <h1 className="text-3xl font-bold mt-3 tracking-tight">IPL 2026 Fantasy</h1>
        <p className="text-sm mt-1.5" style={{ color: "#9CA3AF" }}>186 players &middot; 7 owners &middot; Who wins?</p>
      </div>

      {/* Winner */}
      <div className="rounded-2xl p-5 mb-7 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #FFFBEB, #FEF3C7, #FDE68A)", border: "1px solid #FCD34D" }}>
        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: "#92400E" }}>Predicted Winner</p>
        <h2 className="text-3xl font-extrabold mt-1" style={{ color: "#78350F" }}>{w.name}</h2>
        <p className="mt-2"><span className="text-2xl font-bold" style={{ color: "#B45309" }}>{fmt(w.total)}</span> <span className="text-sm" style={{ color: "#92400E" }}>points</span></p>
        <p className="text-xs mt-2" style={{ color: "#92400E" }}>{w.count} players &middot; {Math.round(w.bat / w.total * 100)}% bat &middot; {Math.round(w.bowl / w.total * 100)}% bowl</p>
      </div>

      {/* Leaderboard table */}
      <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9CA3AF" }}>Leaderboard</p>
      <div className="rounded-xl bg-white overflow-hidden" style={{ border: "1px solid #E5E7EB" }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "#FAFAF9", borderBottom: "1px solid #F3F4F6" }}>
              <th className="text-left py-2.5 px-3 font-medium text-xs" style={{ color: "#9CA3AF" }}>#</th>
              <th className="text-left py-2.5 px-2 font-medium text-xs" style={{ color: "#9CA3AF" }}>Owner</th>
              <th className="text-right py-2.5 px-2 font-medium text-xs" style={{ color: "#9CA3AF" }}>Total</th>
              <th className="text-right py-2.5 px-2 font-medium text-xs" style={{ color: "#3B82F6" }}>Bat</th>
              <th className="text-right py-2.5 px-3 font-medium text-xs" style={{ color: "#10B981" }}>Bowl</th>
            </tr>
          </thead>
          <tbody>
            {data.rankings.map((o, i) => (
              <tr key={o.name} onClick={() => push({ type: "owner", name: o.name })}
                className="cursor-pointer"
                style={{ borderBottom: i < data.rankings.length - 1 ? "1px solid #F3F4F6" : "none" }}>
                <td className="py-3 px-3 font-semibold" style={{ color: OWNER_C[i] }}>{i + 1}</td>
                <td className="py-3 px-2">
                  <span className="font-semibold">{o.name}</span>
                  <span className="text-xs ml-1.5" style={{ color: "#D1D5DB" }}>{o.count}p</span>
                </td>
                <td className="py-3 px-2 text-right font-bold">{fmt(o.total)}</td>
                <td className="py-3 px-2 text-right" style={{ color: "#3B82F6" }}>{fmt(o.bat)}</td>
                <td className="py-3 px-3 text-right" style={{ color: "#10B981" }}>{fmt(o.bowl)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Quick stats */}
      {(() => {
        const mvp = [...data.players].sort((a, b) => b.expTotal - a.expTotal)[0];
        const topB = [...data.players].sort((a, b) => b.expBowl - a.expBowl)[0];
        const gap = Math.round(data.rankings[0].total - data.rankings[1].total);
        return (
          <div className="grid grid-cols-3 gap-2.5 mt-6">
            <QuickStat label="MVP" value={mvp.fn.split(" ").pop() || ""} sub={`${fmt(mvp.expTotal)} pts`} />
            <QuickStat label="Top Bowler" value={topB.fn.split(" ").pop() || ""} sub={`${fmt(topB.expBowl)} pts`} />
            <QuickStat label="Lead" value={`${gap} pts`} sub={`${data.rankings[0].name} ahead`} />
          </div>
        );
      })()}

      {/* Links */}
      <div className="mt-6 space-y-2">
        <LinkBtn label="Search all 186 players" onClick={() => push({ type: "allPlayers" })} />
        <LinkBtn label="How predictions work" onClick={() => push({ type: "method" })} />
        <LinkBtn label="Download all data (CSV)" onClick={() => downloadCSV(data.players)} arrow="&#8595;" />
      </div>

      <p className="text-center text-xs mt-8" style={{ color: "#D1D5DB" }}>Built with Claude &middot; IPL 2026</p>
    </div>
  );
}

function QuickStat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-xl bg-white p-3" style={{ border: "1px solid #F3F4F6" }}>
      <p className="text-xs" style={{ color: "#9CA3AF" }}>{label}</p>
      <p className="font-bold text-sm mt-0.5 truncate">{value}</p>
      <p className="text-xs" style={{ color: "#D1D5DB" }}>{sub}</p>
    </div>
  );
}

function LinkBtn({ label, onClick, arrow = "\u2192" }: { label: string; onClick: () => void; arrow?: string }) {
  return (
    <button onClick={onClick} className="w-full rounded-xl bg-white px-4 py-3 text-sm font-medium flex justify-between items-center card-hover" style={{ border: "1px solid #E5E7EB" }}>
      <span>{label}</span>
      <span style={{ color: "#9CA3AF" }}>{arrow}</span>
    </button>
  );
}

/* ═══════════════════════════
   ALL PLAYERS (Search)
   ═══════════════════════════ */
function AllPlayersScreen({ pop, push }: { pop: () => void; push: (v: View) => void }) {
  const [q, setQ] = useState("");
  const [team, setTeam] = useState("");

  const list = useMemo(() => {
    let l = [...data.players].sort((a, b) => b.expTotal - a.expTotal);
    if (q) { const s = q.toLowerCase(); l = l.filter(p => p.fn.toLowerCase().includes(s) || p.n.toLowerCase().includes(s) || p.owner.toLowerCase().includes(s)); }
    if (team) l = l.filter(p => p.team === team);
    return l;
  }, [q, team]);

  return (
    <div className="px-5 pt-5 pb-10 fade-up">
      <BackBtn onClick={pop} />
      <h2 className="text-2xl font-bold mb-4">All Players</h2>

      <input type="text" placeholder="Search by name or owner..." value={q} onChange={e => setQ(e.target.value)}
        className="w-full rounded-xl bg-white px-4 py-3 text-sm mb-3 focus:outline-none" style={{ border: "1px solid #E5E7EB" }} />

      <div className="flex gap-1.5 overflow-x-auto pb-3 mb-3">
        <FilterPill label="All" active={!team} onClick={() => setTeam("")} />
        {["CSK","MI","SRH","RCB","PBKS","RR","DC","KKR","LSG","GT"].map(t =>
          <FilterPill key={t} label={t} active={team === t} onClick={() => setTeam(team === t ? "" : t)} color={TEAM_C[t]} />
        )}
      </div>

      <p className="text-xs mb-3" style={{ color: "#9CA3AF" }}>{list.length} players</p>

      <div className="rounded-xl bg-white overflow-hidden" style={{ border: "1px solid #E5E7EB" }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "#FAFAF9", borderBottom: "1px solid #F3F4F6" }}>
              <th className="text-left py-2 px-3 font-medium text-xs" style={{ color: "#9CA3AF" }}>Player</th>
              <th className="text-left py-2 px-2 font-medium text-xs" style={{ color: "#9CA3AF" }}>Owner</th>
              <th className="text-right py-2 px-3 font-medium text-xs" style={{ color: "#9CA3AF" }}>Pts</th>
            </tr>
          </thead>
          <tbody>
            {list.slice(0, 50).map((p, i) => (
              <tr key={p.fn} onClick={() => push({ type: "player", player: p })} className="cursor-pointer"
                style={{ borderBottom: "1px solid #F3F4F6" }}>
                <td className="py-2.5 px-3">
                  <div className="flex items-center gap-2">
                    <span className="w-1 h-6 rounded-full flex-shrink-0" style={{ background: TEAM_C[p.team] }} />
                    <div>
                      <p className="font-medium text-sm">{p.fn}</p>
                      <p className="text-xs" style={{ color: "#9CA3AF" }}>{p.team} &middot; {ROLE[p.role] || p.role}{p.avail < 1 ? " &#9888;&#65039;" : ""}</p>
                    </div>
                  </div>
                </td>
                <td className="py-2.5 px-2 text-xs" style={{ color: "#6B7280" }}>{p.owner}</td>
                <td className="py-2.5 px-3 text-right font-bold">{fmt(p.expTotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length > 50 && <p className="text-center text-xs py-3" style={{ color: "#9CA3AF" }}>Showing top 50 of {list.length}. Search to narrow down.</p>}
      </div>
    </div>
  );
}

function FilterPill({ label, active, onClick, color }: { label: string; active: boolean; onClick: () => void; color?: string }) {
  return (
    <button onClick={onClick} className="px-3 py-1.5 rounded-full text-xs font-medium flex-shrink-0 whitespace-nowrap"
      style={active
        ? { background: color || "#1a1a1a", color: "white" }
        : { background: "white", color: color || "#6B7280", border: "1px solid #E5E7EB" }
      }>
      {label}
    </button>
  );
}

/* ═══════════════════════════
   OWNER SCREEN
   ═══════════════════════════ */
function OwnerScreen({ name, pop, push }: { name: string; pop: () => void; push: (v: View) => void }) {
  const od = data.rankings.find(o => o.name === name)!;
  const idx = data.rankings.findIndex(o => o.name === name);
  const color = OWNER_C[idx % OWNER_C.length];

  const players = useMemo(
    () => data.players.filter(p => p.owner === name).sort((a, b) => b.expTotal - a.expTotal),
    [name]
  );

  const guaranteed = players.filter(p => p.tier === "GUARANTEED");
  const likely = players.filter(p => p.tier === "LIKELY");
  const rotation = players.filter(p => p.tier === "ROTATION");
  const unlikely = players.filter(p => p.tier === "UNLIKELY");
  const overseas = players.filter(p => p.overseas).length;
  const injured = players.filter(p => p.avail < 1);

  const batPct = Math.round(od.bat / od.total * 100);

  // Team breakdown
  const teams = useMemo(() => {
    const m: Record<string, { pts: number; count: number }> = {};
    players.forEach(p => {
      if (!m[p.team]) m[p.team] = { pts: 0, count: 0 };
      m[p.team].pts += p.expTotal;
      m[p.team].count++;
    });
    return Object.entries(m).sort((a, b) => b[1].pts - a[1].pts);
  }, [players]);

  return (
    <div className="px-5 pt-5 pb-10 fade-up">
      <BackBtn onClick={pop} />

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold">{name}</h2>
          <p className="text-sm" style={{ color: "#9CA3AF" }}>Rank #{od.rank} &middot; {players.length} players &middot; {overseas} overseas</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold" style={{ color }}>{fmt(od.total)}</p>
          <p className="text-xs" style={{ color: "#9CA3AF" }}>predicted pts</p>
        </div>
      </div>

      {/* Bat / Bowl split */}
      <div className="rounded-xl bg-white p-4 mb-4" style={{ border: "1px solid #E5E7EB" }}>
        <div className="flex justify-between text-xs font-medium mb-1.5">
          <span style={{ color: "#2563EB" }}>Batting {batPct}% &middot; {fmt(od.bat)}</span>
          <span style={{ color: "#059669" }}>Bowling {100 - batPct}% &middot; {fmt(od.bowl)}</span>
        </div>
        <div className="h-2.5 rounded-full overflow-hidden flex" style={{ background: "#F3F4F6" }}>
          <div className="h-full" style={{ width: `${batPct}%`, background: "#3B82F6", borderRadius: "9999px 0 0 9999px" }} />
          <div className="h-full" style={{ width: `${100 - batPct}%`, background: "#10B981", borderRadius: "0 9999px 9999px 0" }} />
        </div>
      </div>

      {/* Teams */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {teams.map(([t, { pts, count }]) => (
          <span key={t} className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ background: TEAM_C[t] + "15", color: TEAM_C[t], border: `1px solid ${TEAM_C[t]}30` }}>
            {t} {count}p &middot; {fmt(pts)}
          </span>
        ))}
      </div>

      {/* Injured players */}
      {injured.length > 0 && (
        <div className="rounded-xl p-3 mb-4" style={{ background: "#FEF2F2", border: "1px solid #FECACA" }}>
          <p className="text-xs font-semibold mb-1" style={{ color: "#DC2626" }}>&#9888;&#65039; Availability Concerns ({injured.length})</p>
          {injured.map(p => (
            <p key={p.fn} className="text-xs" style={{ color: "#991B1B" }}>
              <strong>{p.fn}</strong> — {Math.round(p.avail * 100)}% available{p.avail === 0 ? " (ruled out)" : ""}
            </p>
          ))}
        </div>
      )}

      {/* Player table by tier */}
      {[
        { tier: "GUARANTEED", list: guaranteed },
        { tier: "LIKELY", list: likely },
        { tier: "ROTATION", list: rotation },
        { tier: "UNLIKELY", list: unlikely },
      ].filter(g => g.list.length > 0).map(g => {
        const ti = TIER[g.tier];
        const grpPts = g.list.reduce((s, p) => s + p.expTotal, 0);
        return (
          <div key={g.tier} className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold px-2 py-1 rounded-md" style={{ background: ti.bg, color: ti.color }}>
                {ti.label} ({ti.prob}%)
              </span>
              <span className="text-xs font-medium" style={{ color: "#9CA3AF" }}>{g.list.length} players &middot; {fmt(grpPts)} pts</span>
            </div>
            <div className="rounded-xl bg-white overflow-hidden" style={{ border: "1px solid #E5E7EB" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: "#FAFAF9", borderBottom: "1px solid #F3F4F6" }}>
                    <th className="text-left py-2 px-3 font-medium text-xs" style={{ color: "#9CA3AF" }}>Player</th>
                    <th className="text-right py-2 px-2 font-medium text-xs" style={{ color: "#3B82F6" }}>Bat</th>
                    <th className="text-right py-2 px-2 font-medium text-xs" style={{ color: "#10B981" }}>Bowl</th>
                    <th className="text-right py-2 px-3 font-medium text-xs" style={{ color: "#9CA3AF" }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {g.list.sort((a, b) => b.expTotal - a.expTotal).map((p, i) => (
                    <tr key={p.fn} onClick={() => push({ type: "player", player: p })} className="cursor-pointer"
                      style={{ borderBottom: i < g.list.length - 1 ? "1px solid #F3F4F6" : "none" }}>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <span className="w-1 h-5 rounded-full flex-shrink-0" style={{ background: TEAM_C[p.team] }} />
                          <div>
                            <span className="font-medium">{p.fn}</span>
                            <span className="text-xs ml-1" style={{ color: "#D1D5DB" }}>{p.team}</span>
                            {p.overseas && <span className="text-xs ml-1" style={{ color: "#D97706" }}>&#127757;</span>}
                            {p.avail < 1 && <span className="text-xs ml-1" style={{ color: "#EF4444" }}>&#9888;&#65039;</span>}
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 px-2 text-right" style={{ color: "#3B82F6" }}>{fmt(p.expBat)}</td>
                      <td className="py-2.5 px-2 text-right" style={{ color: "#10B981" }}>{fmt(p.expBowl)}</td>
                      <td className="py-2.5 px-3 text-right font-bold">{fmt(p.expTotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      <button onClick={() => downloadCSV(players, `${name}_squad.csv`)}
        className="w-full rounded-xl bg-white px-4 py-3 mt-3 text-sm font-medium card-hover flex items-center justify-center gap-2"
        style={{ border: "1px solid #E5E7EB" }}>
        Download {name}&apos;s squad (CSV) &#8595;
      </button>
    </div>
  );
}

/* ═══════════════════════════
   PLAYER SCREEN — Full audit
   ═══════════════════════════ */
function PlayerScreen({ player: p, pop }: { player: Player; pop: () => void }) {
  const tc = TEAM_C[p.team] || "#6B7280";
  const ti = TIER[p.tier] || { label: p.tier, color: "#6B7280", bg: "#F3F4F6", prob: 0 };

  return (
    <div className="px-5 pt-5 pb-10 fade-up">
      <BackBtn onClick={pop} />

      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0" style={{ background: tc }}>{p.team}</div>
        <div className="min-w-0">
          <h2 className="text-xl font-bold truncate">{p.fn}</h2>
          <p className="text-xs" style={{ color: "#6B7280" }}>
            {ROLE[p.role] || p.role} &middot; Owned by <strong>{p.owner}</strong>
            {p.overseas ? " \u00B7 Overseas" : ""}
            {p.debutant ? " \u00B7 IPL Debutant" : ""}
          </p>
        </div>
      </div>

      {/* Points summary */}
      <div className="rounded-xl p-5 mb-4 text-center" style={{ background: "#FAFAF9", border: "1px solid #E7E5E4" }}>
        <p className="text-4xl font-extrabold">{fmt(p.expTotal)}</p>
        <p className="text-xs mt-1" style={{ color: "#9CA3AF" }}>predicted points</p>
        <div className="flex justify-center gap-8 mt-4 text-sm">
          <div><span className="font-bold" style={{ color: "#2563EB" }}>{fmt(p.expBat)}</span> <span style={{ color: "#9CA3AF" }}>bat</span></div>
          <div><span className="font-bold" style={{ color: "#059669" }}>{fmt(p.expBowl)}</span> <span style={{ color: "#9CA3AF" }}>bowl</span></div>
          <div><span className="font-bold">{p.expMatches.toFixed(1)}</span> <span style={{ color: "#9CA3AF" }}>matches</span></div>
        </div>
      </div>

      {/* WHY this score — the key section */}
      <Card title="Why this score?">
        <p className="text-sm mb-3" style={{ color: "#6B7280" }}>
          We estimate <strong style={{ color: "#1a1a1a" }}>{p.fn}</strong> plays <strong>{p.expMatches.toFixed(1)}</strong> of 14 matches,
          scoring <strong style={{ color: "#2563EB" }}>{p.runsPerM.toFixed(1)} runs</strong> and taking <strong style={{ color: "#059669" }}>{p.wktsPerM.toFixed(2)} wickets</strong> per match.
        </p>

        <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
          <tbody>
            <Row label="Runs/match" val={p.runsPerM.toFixed(1)} />
            <Row label={`\u00D7 ${p.expMatches.toFixed(1)} matches`} val={fmt(p.expBat)} valColor="#2563EB" bold sub="= batting points" />
            <tr><td colSpan={2} className="py-1"><div style={{ borderTop: "1px solid #F3F4F6" }} /></td></tr>
            <Row label="Wickets/match" val={p.wktsPerM.toFixed(2)} />
            <Row label={`\u00D7 25 pts \u00D7 ${p.expMatches.toFixed(1)} matches`} val={fmt(p.expBowl)} valColor="#059669" bold sub="= bowling points" />
            <tr><td colSpan={2} className="py-1"><div style={{ borderTop: "1px solid #F3F4F6" }} /></td></tr>
            <Row label="Total" val={`${fmt(p.expTotal)} pts`} valColor="#D97706" bold />
          </tbody>
        </table>
      </Card>

      {/* How many matches */}
      <Card title="Expected matches">
        <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
          <tbody>
            <Row label="League matches" val="14" />
            <Row label="Playing XI tier" val={ti.label} valColor={ti.color} />
            <Row label="Selection probability" val={`${ti.prob}%`} />
            <Row label="Availability" val={`${Math.round(p.avail * 100)}%`} valColor={p.avail < 1 ? "#EF4444" : undefined} />
            <tr><td colSpan={2} className="py-1"><div style={{ borderTop: "1px solid #F3F4F6" }} /></td></tr>
            <Row label="14 \u00D7 selection \u00D7 availability" val={`${p.expMatches.toFixed(1)} matches`} bold />
          </tbody>
        </table>
        {p.debutant && <p className="text-xs mt-2" style={{ color: "#7C3AED" }}>IPL debutant &mdash; using baseline estimates for {ROLE[p.role] || p.role} role</p>}
      </Card>

      {/* Availability */}
      {p.availNote && (
        <div className="rounded-xl p-4 mb-4" style={{
          background: p.avail < 1 ? "#FEF2F2" : "#F0FDF4",
          border: `1px solid ${p.avail < 1 ? "#FECACA" : "#BBF7D0"}`
        }}>
          <p className="text-xs font-semibold mb-1" style={{ color: p.avail < 1 ? "#DC2626" : "#16A34A" }}>
            {p.avail < 1 ? "\u26A0\uFE0F Availability" : "\u2705 Available"}
          </p>
          <p className="text-sm leading-relaxed" style={{ color: "#4B5563" }}>{p.availNote}</p>
        </div>
      )}

      {/* IPL Stats */}
      <Card title="IPL career stats">
        <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th className="text-left py-1.5 text-xs font-medium" style={{ color: "#9CA3AF" }}></th>
              <th className="text-right py-1.5 text-xs font-medium" style={{ color: "#9CA3AF" }}>Matches</th>
              <th className="text-right py-1.5 text-xs font-medium" style={{ color: "#3B82F6" }}>Runs</th>
              <th className="text-right py-1.5 text-xs font-medium" style={{ color: "#10B981" }}>Wickets</th>
            </tr>
          </thead>
          <tbody>
            <StatsRow label="Career" matches={p.careerM} runs={p.careerR} wkts={p.careerW} />
            <StatsRow label="IPL 2025" matches={p.s25M} runs={p.s25R} wkts={p.s25W} />
            <StatsRow label="IPL 2024" matches={p.s24M} runs={p.s24R} wkts={p.s24W} />
          </tbody>
        </table>
      </Card>

      {/* Weighting */}
      <Card title="How stats are weighted">
        <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
          <tbody>
            <Row label="IPL 2025 (most recent)" val="50%" valColor="#D97706" />
            <Row label="IPL 2024" val="30%" valColor="#2563EB" />
            <Row label="Career average" val="20%" valColor="#9CA3AF" />
          </tbody>
        </table>
        <p className="text-xs mt-2" style={{ color: "#9CA3AF" }}>If a season is missing, remaining weights normalize to 100%.</p>
      </Card>

      <p className="text-center text-xs mt-4" style={{ color: "#D1D5DB" }}>Confidence: {p.conf}</p>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-white p-4 mb-4" style={{ border: "1px solid #E5E7EB" }}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "#9CA3AF" }}>{title}</p>
      {children}
    </div>
  );
}

function Row({ label, val, valColor, bold, sub }: { label: string; val: string; valColor?: string; bold?: boolean; sub?: string }) {
  return (
    <tr>
      <td className="py-1.5" style={{ color: "#6B7280" }}>
        {label}
        {sub && <span className="text-xs ml-1" style={{ color: "#D1D5DB" }}>{sub}</span>}
      </td>
      <td className={`py-1.5 text-right ${bold ? "font-bold" : "font-medium"}`} style={valColor ? { color: valColor } : {}}>{val}</td>
    </tr>
  );
}

function StatsRow({ label, matches, runs, wkts }: { label: string; matches: number; runs: number; wkts: number }) {
  return (
    <tr style={{ borderBottom: "1px solid #F3F4F6" }}>
      <td className="py-2 text-xs font-medium" style={{ color: "#6B7280" }}>{label}</td>
      <td className="py-2 text-right font-medium">{matches}</td>
      <td className="py-2 text-right font-medium" style={{ color: "#3B82F6" }}>{runs.toLocaleString()}</td>
      <td className="py-2 text-right font-medium" style={{ color: "#10B981" }}>{wkts}</td>
    </tr>
  );
}

function BackBtn({ onClick }: { onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex items-center gap-1 text-sm font-medium mb-4" style={{ color: "#6B7280" }}>
      &larr; Back
    </button>
  );
}

/* ═══════════════════════════
   METHODOLOGY
   ═══════════════════════════ */
function MethodScreen({ pop }: { pop: () => void }) {
  return (
    <div className="px-5 pt-5 pb-10 fade-up">
      <BackBtn onClick={pop} />
      <h2 className="text-2xl font-bold mb-5">How It Works</h2>

      <MBlock title="Scoring">
        Simple: <strong style={{ color: "#2563EB" }}>1 run = 1 point</strong>, <strong style={{ color: "#059669" }}>1 wicket = 25 points</strong>. No bonuses, no strike rate.
      </MBlock>
      <MBlock title="The Formula">
        <code className="block rounded-lg p-3 text-xs" style={{ background: "#FAFAF9", border: "1px solid #F3F4F6" }}>
          Expected Pts = Expected Matches &times; (Runs/Match + Wkts/Match &times; 25)
          <br />Expected Matches = 14 &times; Playing XI % &times; Availability
        </code>
      </MBlock>
      <MBlock title="Stat Weighting">
        50% IPL 2025, 30% IPL 2024, 20% career average. Recent form matters most. Missing seasons normalize the remaining weights.
      </MBlock>
      <MBlock title="Playing XI Tiers">
        <strong style={{ color: "#059669" }}>Locked In (92%)</strong> — captains, franchise stars.{" "}
        <strong style={{ color: "#2563EB" }}>Likely (75%)</strong> — first-choice, may rotate.{" "}
        <strong style={{ color: "#D97706" }}>Fringe (40%)</strong> — competing for spot.{" "}
        <strong style={{ color: "#9CA3AF" }}>Bench (10%)</strong> — deep squad.
      </MBlock>
      <MBlock title="Availability">
        Only reduced for player-specific evidence: injury, international duty, retirement. Assessed via AI analysis of multiple news sources.
      </MBlock>
      <MBlock title="Debutants">
        16 players with no IPL history get baseline estimates by role (e.g. batter: 15 runs/match, bowler: 0.5 wickets/match).
      </MBlock>
      <MBlock title="Not Modeled">
        Venue effects, head-to-head matchups, toss, position changes, Impact Player rule. Over 14 matches these tend to even out.
      </MBlock>
    </div>
  );
}

function MBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h3 className="text-sm font-semibold mb-1.5">{title}</h3>
      <div className="text-sm leading-relaxed" style={{ color: "#6B7280" }}>{children}</div>
    </div>
  );
}
