from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List


def export_static_html(results: List[Dict[str, Any]], stats: Dict[str, Any], output_path: Path) -> None:
    """Gera um relatorio HTML estatico com os resultados da varredura."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    elapsed = "-"
    if stats.get("start_time") and stats.get("end_time"):
        elapsed_seconds = (stats["end_time"] - stats["start_time"]).total_seconds()
        elapsed = f"{elapsed_seconds:.1f}s" if elapsed_seconds < 60 else f"{elapsed_seconds / 60:.1f}min"

    rows = []
    for repo in sorted(results, key=lambda item: item.get("stars", 0), reverse=True):
        topics = repo.get("topics") or []
        if isinstance(topics, str):
            topics = [topics]

        name = escape(repo.get("name") or repo.get("full_name") or "Desconhecido")
        full_name = escape(repo.get("full_name") or "")
        description = escape(repo.get("description") or "Sem descricao")
        language = escape(repo.get("language") or "Unknown")
        url = escape(repo.get("url") or repo.get("html_url") or "")
        source_query = escape(repo.get("source_query") or "")
        stars = int(repo.get("stars", 0) or 0)
        topics_text = ", ".join(escape(str(topic)) for topic in topics[:5]) if topics else "-"

        rows.append(
            "<tr>"
            f"<td><a href='{url}' target='_blank' rel='noreferrer'>{name}</a><div class='muted'>{full_name}</div></td>"
            f"<td>{description}</td>"
            f"<td>{language}</td>"
            f"<td>{stars}</td>"
            f"<td>{topics_text}</td>"
            f"<td>{source_query}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang='pt-BR'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>OSINT Tool Finder - Relatorio</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #0a1324; color: #e8efff; }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    .hero {{ background: linear-gradient(120deg, #11315a, #153b4f); padding: 24px; border-radius: 14px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 16px 0; }}
    .card {{ background: #101d36; border: 1px solid #2a395a; border-radius: 12px; padding: 14px; }}
    .label {{ color: #93a5c3; font-size: 12px; text-transform: uppercase; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 6px; }}
    .table-wrap {{ overflow-x: auto; background: #101d36; border: 1px solid #2a395a; border-radius: 12px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1024px; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #2a395a; text-align: left; }}
    th {{ color: #98abd0; font-size: 12px; text-transform: uppercase; }}
    a {{ color: #7ad7ff; }}
    .muted {{ font-size: 12px; color: #98abd0; }}
    @media (max-width: 760px) {{ .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
  </style>
</head>
<body>
  <main class='wrap'>
    <section class='hero'>
      <h1>OSINT Tool Finder</h1>
      <p>Relatorio estatico da varredura publica.</p>
    </section>
    <section class='stats'>
      <div class='card'><div class='label'>Termos</div><div class='value'>{len(stats.get('queries', []))}</div></div>
      <div class='card'><div class='label'>Resultados</div><div class='value'>{len(results)}</div></div>
      <div class='card'><div class='label'>Encontrados</div><div class='value'>{stats.get('total_found', 0)}</div></div>
      <div class='card'><div class='label'>Tempo</div><div class='value'>{escape(elapsed)}</div></div>
    </section>
    <section class='table-wrap'>
      <table>
        <thead>
          <tr><th>Repositorio</th><th>Descricao</th><th>Linguagem</th><th>Stars</th><th>Topicos</th><th>Query</th></tr>
        </thead>
        <tbody>
          {''.join(rows) if rows else "<tr><td colspan='6'>Nenhum resultado.</td></tr>"}
        </tbody>
      </table>
    </section>
    <p class='muted'>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {escape(str(output_path.as_posix()))}</p>
  </main>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
