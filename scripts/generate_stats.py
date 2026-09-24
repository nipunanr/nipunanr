#!/usr/bin/env python3
"""Generate self-hosted stats, languages, streak and trophy SVG cards for a GitHub profile.
Usage: GH_TOKEN=... python scripts/generate_stats.py <username> [--placeholder | --demo]
Output: assets/generated/{stats,languages,streak,trophies}.svg
"""
import json, os, sys, urllib.request
from datetime import date, timedelta
from html import escape

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "generated")
BG, BORDER, TEAL, TXT, MUTED = "#050d1f", "#16305f", "#00ABC9", "#ffffff", "#9fb4d9"
FONT = "font-family=\"'Segoe UI',Roboto,Helvetica,Arial,sans-serif\""
QUERY = """
query($login:String!,$after:String){
  user(login:$login){
    name followers{totalCount}
    pullRequests{totalCount} issues{totalCount}
    contributionsCollection{
      totalCommitContributions restrictedContributionsCount
      contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}
    }
    repositories(ownerAffiliations:OWNER,isFork:false,first:100,after:$after){
      totalCount pageInfo{hasNextPage endCursor}
      nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}
    }
  }
}"""

def gql(token, login, after=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login, "after": after}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]

def fetch(token, login):
    u = gql(token, login)
    repos = list(u["repositories"]["nodes"])
    while u["repositories"]["pageInfo"]["hasNextPage"]:
        more = gql(token, login, u["repositories"]["pageInfo"]["endCursor"])
        repos += more["repositories"]["nodes"]
        u["repositories"]["pageInfo"] = more["repositories"]["pageInfo"]
    cc = u["contributionsCollection"]
    days = sorted((d["date"], d["contributionCount"]) for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"])
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#888888"])[0] += e["size"]
    cur = longest = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    today = date.today().isoformat()
    seq = [c for d, c in days if d <= today]
    if seq and seq[-1] == 0:
        seq = seq[:-1]
    for c in reversed(seq):
        if c > 0: cur += 1
        else: break
    return {
        "name": u["name"] or login, "login": login,
        "stars": sum(r["stargazerCount"] for r in repos), "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"], "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "contribs": cc["contributionCalendar"]["totalContributions"],
        "cur": cur, "longest": longest, "langs": sorted(langs.items(), key=lambda kv: -kv[1][0]),
    }

def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(title)}">'
            f'<style>.fade{{animation:f .8s ease-out both}}@keyframes f{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}'
            f'.grow{{transform-box:fill-box;transform-origin:left center;animation:g 1.2s ease-out both}}@keyframes g{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}</style>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{BORDER}"/>{body}</svg>')

def fmt(n): return f"{n:,}"

def stats_card(d):
    rows = [("Total stars", d["stars"]), ("Commits (last year)", d["commits"]), ("Pull requests", d["prs"]),
            ("Issues", d["issues"]), ("Public repos", d["repos"]), ("Followers", d["followers"])]
    b = f'<text x="24" y="38" font-size="18" font-weight="700" fill="{TEAL}" {FONT}>{escape(d["name"])}\'s GitHub Stats</text>'
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 26
        b += (f'<g class="fade" style="animation-delay:{i*.1:.1f}s"><circle cx="30" cy="{y-5}" r="5" fill="{TEAL}"/>'
              f'<text x="46" y="{y}" font-size="14" fill="{MUTED}" {FONT}>{k}</text>'
              f'<text x="396" y="{y}" font-size="14" font-weight="700" fill="{TXT}" text-anchor="end" {FONT}>{fmt(v)}</text></g>')
    return svg(420, 230, b, "GitHub stats")

def langs_card(d):
    tot = sum(s for _, (s, _) in d["langs"]) or 1
    top = d["langs"][:6]
    b = f'<text x="24" y="38" font-size="18" font-weight="700" fill="{TEAL}" {FONT}>Top Languages</text>'
    x = 24.0
    b += '<clipPath id="c"><rect x="24" y="56" width="372" height="12" rx="6"/></clipPath><g clip-path="url(#c)">'
    for n, (s, c) in top:
        w = 372 * s / tot
        b += f'<rect class="grow" x="{x:.1f}" y="56" width="{w:.1f}" height="12" fill="{c}"/>'
        x += w
    b += '</g>'
    for i, (n, (s, c)) in enumerate(top):
        col, row = i % 2, i // 2
        px, py = 24 + col * 190, 96 + row * 26
        b += (f'<g class="fade" style="animation-delay:{i*.1:.1f}s"><circle cx="{px+5}" cy="{py-5}" r="5" fill="{c}"/>'
              f'<text x="{px+18}" y="{py}" font-size="13" fill="{TXT}" {FONT}>{escape(n)} <tspan fill="{MUTED}">{100*s/tot:.1f}%</tspan></text></g>')
    if not top:
        b += f'<text x="24" y="100" font-size="13" fill="{MUTED}" {FONT}>No language data yet</text>'
    return svg(420, 230, b, "Top languages")

def streak_card(d):
    items = [("Contributions (last year)", d["contribs"]), ("Current streak", d["cur"]), ("Longest streak", d["longest"])]
    b = ""
    for i, (k, v) in enumerate(items):
        cx = 150 + i * 300
        b += (f'<g class="fade" style="animation-delay:{i*.2:.1f}s"><text x="{cx}" y="72" font-size="40" font-weight="800" fill="{TEAL}" text-anchor="middle" {FONT}>{fmt(v)}</text>'
              f'<text x="{cx}" y="102" font-size="14" fill="{MUTED}" text-anchor="middle" {FONT}>{k}</text></g>')
    return svg(900, 130, b, "Contribution streak")

TIERS = [("Bronze", "#cd7f32"), ("Silver", "#c0c0c0"), ("Gold", "#ffd24a"), ("Platinum", "#7ee7ff"), ("Diamond", "#a78bfa")]
def trophies_card(d):
    spec = [("Stars", d["stars"], [1, 10, 50, 200, 1000]), ("Commits", d["commits"], [50, 250, 750, 2000, 5000]),
            ("Followers", d["followers"], [1, 10, 50, 200, 1000]), ("Repos", d["repos"], [1, 10, 30, 75, 150]),
            ("Pull Requests", d["prs"], [1, 20, 100, 500, 1500]), ("Issues", d["issues"], [1, 10, 50, 200, 800]),
            ("Streak", d["longest"], [3, 14, 30, 100, 250])]
    b = ""
    for i, (label, val, th) in enumerate(spec):
        lvl = sum(val >= t for t in th)
        col = TIERS[lvl - 1][1] if lvl else "#3a4a6b"
        tier = TIERS[lvl - 1][0] if lvl else "Locked"
        cx = 60 + i * 130
        b += (f'<g class="fade" style="animation-delay:{i*.12:.2f}s" transform="translate({cx},0)">'
              f'<g transform="translate(0,58)" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round">'
              f'<path d="M-16 -24h32v14a16 16 0 0 1-32 0z" fill="{col}" fill-opacity=".2"/><path d="M-16 -18h-8a8 8 0 0 0 8 14M16 -18h8a8 8 0 0 1-8 14M0 6v12M-10 20h20"/></g>'
              f'<text y="98" font-size="13" font-weight="700" fill="{TXT}" text-anchor="middle" {FONT}>{label}</text>'
              f'<text y="116" font-size="12" fill="{col}" text-anchor="middle" {FONT}>{tier} - {fmt(val)}</text></g>')
    return svg(900, 140, b, "GitHub trophies")

def placeholder():
    return {"name": "Nipuna", "login": "", "stars": 0, "repos": 0, "followers": 0, "prs": 0, "issues": 0,
            "commits": 0, "contribs": 0, "cur": 0, "longest": 0, "langs": []}

def write(d):
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("stats", stats_card), ("languages", langs_card), ("streak", streak_card), ("trophies", trophies_card)):
        with open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn(d))

if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        write(placeholder()); sys.exit(0)
    if "--demo" in sys.argv:
        d = placeholder(); d.update(stars=12, commits=640, followers=30, repos=22, prs=41, issues=9, contribs=812, cur=6, longest=41,
                                    langs=[("Python", [5000, "#3572A5"]), ("JavaScript", [3000, "#f1e05a"]), ("Dart", [1500, "#00B4AB"])])
        write(d); sys.exit(0)
    user = next(a for a in sys.argv[1:] if not a.startswith("--"))
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok: sys.exit("GH_TOKEN is required")
    write(fetch(tok, user))
