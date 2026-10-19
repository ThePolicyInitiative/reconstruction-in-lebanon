"""Small, local SVG graphics: no remote images, scripts or tracking."""
from html import escape
from base64 import b64encode

PATHS = {
    "energy": '<path d="m13 2-9 12h7l-1 8 10-13h-7z"/>',
    "education": '<path d="M12 6v15M3 4c4-1 6 0 9 2 3-2 5-3 9-2v15c-4-1-6 0-9 2-3-2-5-3-9-2z"/>',
    "cedar": '<path d="M12 2 8 7h2L5 12h4l-6 5h8v5h2v-5h8l-6-5h4l-5-5h2z" fill="currentColor" stroke="none"/>',
    "arrow": '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    "external": '<path d="M14 4h6v6M20 4 10 14M10 4H4v16h16v-6"/>',
    "shield": '<path d="m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7z"/><path d="m8 12 3 3 5-6"/>',
    "services": '<path d="M3 21h18M5 21V9h14v12M9 9V4h6v5M9 15h6m-3-3v6"/>',
    "building": '<path d="M3 21h18M5 21V9h8v12m0-17h6v17M7 6h4M8 12h2m-2 4h2m6-9h1m-1 4h1m-1 4h1"/>',
    "oversight": '<path d="M4 5h16v14H4zM8 9h8M8 13h3m3 1 2 2 4-4"/>',
    "family": '<circle cx="8" cy="7" r="3"/><circle cx="17" cy="9" r="2"/><path d="M2 21v-4a6 6 0 0 1 12 0v4m1-7a5 5 0 0 1 7 4v3"/>',
    "road": '<path d="m7 3-4 18m14-18 4 18M12 3v3m0 4v4m0 4v3"/>',
    "growth": '<path d="M4 20V4m0 16h17M8 15l4-5 4 2 5-7m-4 0h4v4"/>',
    "pin": '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18M7 14h3m4 0h3"/>',
    "people": '<circle cx="9" cy="7" r="3"/><path d="M3 21v-4a6 6 0 0 1 12 0v4m1-17a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 5v2"/>',
    "fund": '<circle cx="12" cy="12" r="9"/><path d="M15 8H10a2 2 0 0 0 0 4h4a2 2 0 0 1 0 4H9m3-11v14"/>',
}


def svg_image(svg, alt="", size=None):
    # st.html sanitizes inline SVG. A local SVG image preserves the graphic.
    data = b64encode(svg.encode("utf-8")).decode("ascii")
    dimensions = f' width="{size}" height="{size}"' if size else ""
    return f'<img src="data:image/svg+xml;base64,{data}" alt="{escape(alt, quote=True)}"{dimensions}/>'


def icon(name, size=24, color=None):
    color = color or ("#ffffff" if name == "cedar" else "#17634f")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{PATHS[name].replace("currentColor", color)}</svg>'
    return svg_image(svg, size=size)


def funding_ring(percent):
    # The ring denotes financing coverage only, never construction progress.
    label = escape(f"{percent:.0f}% of the LEAP framework covered by initial approved financing")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><circle cx="100" cy="100" r="82" fill="none" stroke="#3c5948" stroke-width="15"/>
    <circle cx="100" cy="100" r="82" pathLength="100" fill="none" stroke="#bad098" stroke-width="15" stroke-dasharray="{percent} {100-percent}"/></svg>'''
    return f'''<div class="funding-ring" role="img" aria-label="{label}">{svg_image(svg)}
    <div class="ring-label"><strong>{percent:.0f}%</strong><span>initial financing coverage</span></div></div>'''


def reconstruction_art():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 470 310">
    <circle cx="257" cy="157" r="130" fill="#dce5d1"/><circle cx="257" cy="157" r="98" fill="none" stroke="#c7d5b9" stroke-dasharray="3 7"/>
    <path d="M35 258h398" stroke="#a5b99e" stroke-width="1.5"/>
    <path d="M96 250V135l50-28 49 28v115z" fill="#f7f7ec" stroke="#749575" stroke-width="1.5"/>
    <path d="m86 138 60-36 60 36" stroke="#426c52" stroke-width="4" fill="none"/>
    <path d="M114 151h20v29h-20zm42 0h20v29h-20z" fill="#b8cba9"/>
    <path d="M135 211a12 12 0 0 1 24 0v39h-24z" fill="#65866a"/>
    <path d="M217 250V97h80v153" fill="#cedbc0" stroke="#749575" stroke-width="1.5"/>
    <path d="M232 113h16v25h-16zm33 0h16v25h-16zm-33 43h16v25h-16zm33 0h16v25h-16zm-33 44h16v25h-16zm33 0h16v25h-16z" fill="#799d79"/>
    <path d="M321 250V66m-7 0h14m-7 17 16 14-16 14 16 14-16 14 16 14-16 14 16 14-16 14 16 14-16 14m16 13V66" stroke="#587750" stroke-width="2" fill="none"/>
    <path d="M229 66h164v10H229zM262 66l66-28 56 28M328 38v28" fill="none" stroke="#587750" stroke-width="2"/>
    <path d="M263 76v24m-5 0h10m-5 0v7" stroke="#587750" stroke-width="2"/>
    <path d="M305 250h44" stroke="#587750" stroke-width="3"/>
    <path d="m372 163-15 24h9l-20 24h15l-26 23h33v21h7v-21h34l-27-23h16l-20-24h9z" fill="#31684c"/>
    <path d="M52 254v-21m-5-12h10l7 12H40z" fill="#a7604a"/><path d="M64 249h19" stroke="#a7604a" stroke-width="3"/>
    <rect x="59" y="66" width="96" height="31" rx="15.5" fill="#fff" fill-opacity=".8"/>
    <circle cx="77" cy="81" r="4" fill="#54835e"/><text x="88" y="85" fill="#40694d" font-size="10" font-family="Arial,sans-serif">LEBANON</text>
    <circle cx="404" cy="126" r="16" fill="#f6f7ed"/><path d="M398 126h12m-6-6v12" stroke="#678b61" stroke-width="1.5"/>
    </svg>'''
    return svg_image(svg, "Illustration of homes, a cedar tree and a construction crane")
