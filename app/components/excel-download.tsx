"use client";

type Player = {
  fn: string;
  n: string;
  team: string;
  owner: string;
  role: string;
  overseas: boolean;
  tier: string;
  avail: number;
  availNote: string;
  conf: string;
  careerM: number;
  careerR: number;
  careerW: number;
  s25M: number;
  s25R: number;
  s25W: number;
  s24M: number;
  s24R: number;
  s24W: number;
  expMatches: number;
  expBat: number;
  expBowl: number;
  expTotal: number;
  runsPerM: number;
  wktsPerM: number;
  debutant: boolean;
};

export function downloadCSV(players: Player[], filename: string = "ipl_fantasy_predictions.csv") {
  const headers = [
    "Fantasy Owner", "Player", "Nickname", "IPL Team", "Role", "Overseas",
    "Playing XI Tier", "Availability %", "Availability Note", "Debutant",
    "Career Matches", "Career Runs", "Career Wickets",
    "IPL 2025 Matches", "IPL 2025 Runs", "IPL 2025 Wickets",
    "IPL 2024 Matches", "IPL 2024 Runs", "IPL 2024 Wickets",
    "Weighted Runs/Match", "Weighted Wickets/Match",
    "Expected Matches", "Expected Batting Pts", "Expected Bowling Pts", "Expected Total Pts",
    "Confidence"
  ];

  const rows = [...players]
    .sort((a, b) => b.expTotal - a.expTotal)
    .map((p) => [
      p.owner, p.fn, p.n, p.team, p.role, p.overseas ? "Yes" : "No",
      p.tier, Math.round(p.avail * 100), `"${p.availNote.replace(/"/g, '""')}"`, p.debutant ? "Yes" : "No",
      p.careerM, p.careerR, p.careerW,
      p.s25M, p.s25R, p.s25W,
      p.s24M, p.s24R, p.s24W,
      p.runsPerM.toFixed(1), p.wktsPerM.toFixed(2),
      p.expMatches.toFixed(1), p.expBat.toFixed(1), p.expBowl.toFixed(1), p.expTotal.toFixed(1),
      p.conf
    ]);

  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function DownloadButton({ players, label = "Download Full Data (CSV)", filename }: {
  players: Player[];
  label?: string;
  filename?: string;
}) {
  return (
    <button
      onClick={() => downloadCSV(players, filename)}
      className="w-full rounded-xl bg-gray-800 border border-gray-700 px-4 py-3 text-sm font-medium hover:bg-gray-700 transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
    >
      <span>{"\ud83d\udcc1"}</span>
      <span>{label}</span>
    </button>
  );
}
