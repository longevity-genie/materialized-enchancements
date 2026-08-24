from __future__ import annotations

import reflex as rx

from materialized_enhancements.components.layout import fomantic_icon, template
from materialized_enhancements.artex import artex_publish_button
from materialized_enhancements.crawler_assets import OG_PREVIEW_SIZE, OG_PREVIEW_URL_PATH, PUBLIC_ROUTES
from materialized_enhancements.env import public_app_url
from materialized_enhancements.gene_data import (
    CATEGORY_PRICES,
    GAME_CATEGORY_COUNTS,
    GAME_CATEGORY_DISPLAY_COUNTS,
    DEFAULT_BUDGET,
    GENE_LIBRARY,
    UNIQUE_CATEGORIES,
)
from materialized_enhancements.env import (
    DISCORD_INVITE_URL,
    DONATION_URL,
    GITHUB_PROJECT_URL,
)
from materialized_enhancements.pages.knowledgebase import (
    KnowledgebaseState,
    knowledgebase_layout,
)
from materialized_enhancements.state import (
    CATEGORY_COLORS,
    CATEGORY_DESCRIPTIONS,
    CATEGORY_ICONS,
    AppState,
    ComposeState,
)

_CONTENT_STYLE: dict = {
    "maxWidth": "min(54rem, 94vw)",
    "margin": "0 auto",
    "padding": "0 1.35rem",
}

_ROUTE_METADATA = {route.path: route for route in PUBLIC_ROUTES}
_SITE_TITLE = "Materialized Enhancements"
_REPORT_PORTRAIT_UPLOAD_ID = "report-portrait-upload"
_HERO_PORTRAIT_UPLOAD_ID = "hero-portrait-upload"


def _page_meta(route_path: str) -> list[dict[str, str]]:
    base = public_app_url()
    route = _ROUTE_METADATA[route_path]
    title = _SITE_TITLE if route_path == "/" else f"{_SITE_TITLE} | {route.title}"
    image_url = _page_image_url()
    canonical_url = f"{base}/" if route_path == "/" else f"{base}{route_path}"
    return [
        {"name": "robots", "content": "index, follow"},
        {"property": "og:type", "content": "website"},
        {"property": "og:site_name", "content": _SITE_TITLE},
        {"property": "og:title", "content": title},
        {"property": "og:description", "content": route.description},
        {"property": "og:url", "content": canonical_url},
        {"property": "og:image", "content": image_url},
        {"property": "og:image:type", "content": "image/png"},
        {"property": "og:image:width", "content": str(OG_PREVIEW_SIZE[0])},
        {"property": "og:image:height", "content": str(OG_PREVIEW_SIZE[1])},
        {"property": "og:image:alt", "content": "Materialized Enhancements social preview card."},
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:title", "content": title},
        {"name": "twitter:description", "content": route.description},
        {"name": "twitter:image", "content": image_url},
        {"name": "twitter:image:alt", "content": "Materialized Enhancements social preview card."},
    ]


def _page_image_url() -> str:
    return f"{public_app_url()}{OG_PREVIEW_URL_PATH}?v=2"


def _category_tooltip(category: str) -> str:
    description = CATEGORY_DESCRIPTIONS.get(category, "Genetic enhancement category.")
    return f"{category}: {description}"


def _page_title(route_path: str) -> str:
    return _SITE_TITLE if route_path == "/" else f"{_SITE_TITLE} | {_ROUTE_METADATA[route_path].title}"


def _page_description(route_path: str) -> str:
    return _ROUTE_METADATA[route_path].description


def _email_send_form(
    state_cls: type,
    *,
    accent_class: str = "ui primary button",
    placeholder: str = "you@example.com",
    button_label: str = "Send to email",
) -> rx.Component:
    """Email recipient input + Send button. Mirrors the Download button.

    Wires into ``state_cls`` attributes:
      ``recipient_email``, ``email_sending``, ``email_sent``, ``email_error``,
      ``can_send_email``, setter ``set_recipient_email``, and one of
      ``send_sculpture_email`` / ``send_jigsaw_email`` (auto-selected by name).
    """
    # Sculpture goes through start_email_send (which builds the PDF in the
    # browser, then chains into send_sculpture_email). Jigsaw sends directly.
    send_handler = getattr(state_cls, "start_email_send", None) or getattr(
        state_cls, "send_jigsaw_email"
    )
    return rx.el.div(
        rx.el.div(
            rx.el.input(
                class_name="me-email-send-input",
                type="email",
                placeholder=placeholder,
                value=state_cls.recipient_email,
                on_change=state_cls.set_recipient_email,
                style={
                    "flex": "1",
                    "minWidth": "0",
                    "padding": "9px 12px",
                    "borderRadius": "6px",
                    "border": "1px solid #d1d5db",
                    "fontSize": "0.88rem",
                    "outline": "none",
                    "backgroundColor": "#ffffff",
                    "color": "#1a1a2e",
                },
            ),
            rx.el.button(
                rx.cond(
                    state_cls.email_sending,
                    fomantic_icon("sync", size=14, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("paper plane", size=14),
                ),
                rx.el.span(
                    rx.cond(state_cls.email_sending, " Sending\u2026", f" {button_label}"),
                    style={"marginLeft": "6px"},
                ),
                on_click=send_handler,
                class_name=rx.cond(
                    state_cls.email_sending,
                    f"ui disabled {accent_class.removeprefix('ui ')}",
                    accent_class,
                ),
                type="button",
                style={"padding": "12px 18px", "fontSize": "0.96rem", "fontWeight": "900", "whiteSpace": "nowrap"},
            ),
            class_name="me-email-send-row",
            style={"display": "flex", "gap": "8px", "alignItems": "stretch"},
        ),
        rx.cond(
            state_cls.email_sent,
            rx.el.div(
                fomantic_icon("check circle", size=12, color="#16a085"),
                rx.el.span(
                    " Sent — check your inbox.",
                    style={"marginLeft": "4px"},
                ),
                style={
                    "marginTop": "6px",
                    "fontSize": "1.02rem",
                    "color": "#16a085",
                    "fontWeight": "600",
                },
            ),
            rx.fragment(),
        ),
        rx.cond(
            state_cls.email_error != "",
            _inline_notice(state_cls.email_error),
            rx.fragment(),
        ),
        class_name="me-email-send-form",
        style={"marginTop": "0"},
    )


# ── Tab 0: Landing (nav label: About) ───────────────────────────────────────


def _roadmap_item(title: str, detail: str) -> rx.Component:
    return rx.el.li(
        rx.el.strong(title, style={"color": "#f8fafc"}),
        f" — {detail}",
        style={
            "color": "#cbd5e1",
            "fontSize": "0.98rem",
            "lineHeight": "1.6",
            "marginBottom": "8px",
        },
    )


def _contact_link(label: str, href: str) -> rx.Component:
    external_attrs: dict[str, str] = (
        {"target": "_blank", "rel": "noopener noreferrer"}
        if href.startswith("http")
        else {}
    )
    return rx.el.a(
        label,
        href=href,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "padding": "9px 12px",
            "borderRadius": "999px",
            "border": "1px solid rgba(196, 181, 253, 0.38)",
            "background": "rgba(124, 58, 237, 0.14)",
            "color": "#ddd6fe",
            "fontSize": "0.86rem",
            "fontWeight": "800",
            "textDecoration": "none",
        },
        **external_attrs,
    )


def _landing_tab() -> rx.Component:
    _p_muted = {
        "color": "#6b7280",
        "fontSize": "1.05rem",
        "lineHeight": "1.7",
        "marginBottom": "12px",
    }
    _p_body = {
        "color": "#374151",
        "fontSize": "1rem",
        "lineHeight": "1.65",
        "marginBottom": "12px",
    }
    _a = {"color": "#7c3aed", "fontWeight": "600", "textDecoration": "underline"}
    _sidebar_card = {
        "padding": "14px",
        "borderRadius": "14px",
        "border": "1px solid rgba(148, 163, 184, 0.22)",
        "background": "rgba(15, 23, 42, 0.54)",
        "boxShadow": "0 14px 34px rgba(2, 6, 23, 0.18)",
    }
    _sidebar_title = {
        "fontSize": "0.86rem",
        "fontWeight": "900",
        "letterSpacing": "0.08em",
        "textTransform": "uppercase",
        "color": "#e9d5ff",
        "margin": "0 0 10px 0",
    }
    _qr_card = {
        "display": "block",
        "padding": "14px",
        "background": "rgba(2, 6, 23, 0.42)",
        "borderRadius": "12px",
        "border": "1px solid rgba(196, 181, 253, 0.24)",
        "textDecoration": "none",
    }
    _qr_image = {
        "width": "min(100%, 190px)",
        "height": "auto",
        "aspectRatio": "1 / 1",
        "objectFit": "cover",
        "display": "block",
        "borderRadius": "8px",
        "margin": "0 auto 10px auto",
        "boxShadow": "0 2px 10px rgba(0,0,0,0.22)",
    }
    _team_grid = {
        "display": "grid",
        "gridTemplateColumns": "1fr",
        "gap": "12px",
    }
    _team_member_card = {
        "display": "flex",
        "alignItems": "flex-start",
        "gap": "12px",
    }
    _team_photo = {
        "width": "64px",
        "height": "64px",
        "objectFit": "cover",
        "borderRadius": "999px",
        "border": "1px solid rgba(196, 181, 253, 0.36)",
        "boxShadow": "0 8px 18px rgba(2, 6, 23, 0.28)",
        "backgroundColor": "rgba(2, 6, 23, 0.38)",
    }
    _team_photo_link = {
        "display": "block",
        "width": "64px",
        "height": "64px",
        "flex": "0 0 64px",
        "borderRadius": "999px",
        "lineHeight": "0",
    }
    _team_text = {
        "color": "#cbd5e1",
        "fontSize": "1rem",
        "lineHeight": "1.65",
        "margin": "0",
    }

    def _team_member(
        name: str,
        role: str,
        image_src: str | None = None,
        image_alt: str | None = None,
        link_href: str | None = None,
    ) -> rx.Component:
        name_label: rx.Component = rx.el.strong(name)
        if link_href:
            name_label = rx.el.strong(
                rx.el.a(
                    name,
                    href=link_href,
                    target="_blank",
                    rel="noopener noreferrer",
                    style=_a,
                ),
            )
        text = rx.el.p(
            name_label,
            f" — {role}",
            style=_team_text,
        )
        if not image_src:
            return rx.el.div(text, style=_team_member_card)
        photo: rx.Component = rx.el.img(
            src=image_src,
            alt=image_alt or name,
            loading="lazy",
            decoding="async",
            style=_team_photo,
        )
        if link_href:
            photo = rx.el.a(
                photo,
                href=link_href,
                target="_blank",
                rel="noopener noreferrer",
                aria_label=f"{name} profile",
                style=_team_photo_link,
            )
        return rx.el.div(
            photo,
            text,
            style=_team_member_card,
        )

    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        "Materialized Enhancements",
                        style={
                            "color": "#1a1a2e",
                            "fontSize": "2.4rem",
                            "fontWeight": "800",
                            "marginBottom": "4px",
                        },
                    ),
                    rx.el.p(
                        "Real genes. Real science. Your character. A printable crystal from your choices.",
                        style={
                            "color": "#7c3aed",
                            "fontSize": "1.25rem",
                            "fontWeight": "800",
                            "lineHeight": "1.5",
                            "marginBottom": "14px",
                            "letterSpacing": "0.01em",
                        },
                    ),
                    rx.el.p(
                        "Upgrading human DNA is not science fiction — it is already happening in adults today. "
                        "In alternative jurisdictions like Prospera, medical tourists are actively receiving gene "
                        "therapies for muscle growth (Follistatin) and blood vessel creation (VEGF). "
                        "The next decade will bring harder questions about what traits people might choose. "
                        "Nature already has the code for extreme survival: shark longevity, tardigrade radiation "
                        "shields, whale DNA repair, axolotl regeneration, and bat immune tolerance.",
                        style=_p_body,
                    ),
                    rx.el.p(
                        rx.fragment(
                            rx.el.strong("Materialized Enhancements", style={"color": "#1a1a2e"}),
                            " is an RPG-style character creator for speculative human enhancement. "
                            "Every gene card cites peer-reviewed papers, shows a tiered evidence grade (T2–T6), "
                            "and is upfront about contradictions and translational gaps. "
                            "Spend enhancement credits on real genes from extraordinary organisms, "
                            "watch your profile light up by category, then materialize the result as a "
                            "unique printable crystal (an abstract form grown from your gene choices — "
                            "not a full-body figure yet) and a personal enhancement report.",
                        ),
                        style=_p_body,
                    ),
                    rx.el.p(
                        "Developed by the joint GlucoseDAO and Longevity Genie team.",
                        style={"color": "#7c3aed", "fontSize": "0.95rem", "fontWeight": "600", "marginBottom": "18px"},
                    ),
                    rx.el.div(
                        rx.el.iframe(
                            src="https://www.youtube.com/embed/ev726lz5sLo",
                            title="Materialized Enhancements",
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
                            allow_full_screen=True,
                            style={
                                "position": "absolute",
                                "top": "0",
                                "left": "0",
                                "width": "100%",
                                "height": "100%",
                                "border": "none",
                                "borderRadius": "10px",
                            },
                        ),
                        style={
                            "width": "100%",
                            "maxWidth": "1200px",
                            "aspectRatio": "16 / 9",
                            "position": "relative",
                            "backgroundColor": "#000",
                            "borderRadius": "10px",
                            "margin": "0 auto 18px auto",
                            "overflow": "hidden",
                            "boxShadow": "0 16px 36px rgba(2, 6, 23, 0.28)",
                        },
                    ),
                    rx.el.p(
                        "Learn real genetics in a playful way: browse enhancement genes with scientific evidence "
                        "tiers, peer-reviewed citations, and notes on contradictions — see how they are grouped "
                        "by biological function, then take home a unique souvenir — a printable crystal "
                        "grown from your choices, plus a personal report. A full-body 3D figure that shows "
                        "your traits is on the roadmap; today the materialization is this abstract crystal.",
                        style={**_p_muted, "marginBottom": "16px"},
                    ),
                    rx.el.p(
                        "We also do a lot of open-source work across personalized genomics, aging research, "
                        "bio AI agents, glucose prediction, and parametric art. For parametric art and glucose prediction, see ",
                        rx.el.a(
                            "Livia Zaharia's work",
                            href="http://livia.glucosedao.org/",
                            target="_blank",
                            rel="noopener noreferrer",
                            style=_a,
                        ),
                        ".",
                        style={**_p_body, "marginBottom": "16px"},
                    ),
                    rx.el.div(
                        rx.el.h2(
                            "Want to collaborate, contribute, or report a mistake?",
                            style={
                                "color": "#1a1a2e",
                                "fontSize": "1.35rem",
                                "fontWeight": "900",
                                "margin": "0 0 8px 0",
                            },
                        ),
                        rx.el.p(
                            "The gene list is not complete, and the project is meant to grow. If you found a missing "
                            "gene, a questionable annotation, a useful paper, or want to collaborate on art, science, "
                            "education, venues, fabrication, or new generative models, open a GitHub issue or talk to us directly.",
                            style={**_p_body, "marginBottom": "12px"},
                        ),
                        rx.el.div(
                            _contact_link(
                                "Open a GitHub issue",
                                "https://github.com/longevity-genie/materialized-enhancements/issues",
                            ),
                            _contact_link("Email Livia", "mailto:liviazaharia2020@gmail.com"),
                            _contact_link("Email Anton", "mailto:antonkulaga@gmail.com"),
                            _contact_link(
                                "Livia on LinkedIn",
                                "https://www.linkedin.com/in/livia-zaharia-4b1425a0/",
                            ),
                            _contact_link(
                                "Anton on LinkedIn",
                                "https://www.linkedin.com/in/antonkulaga/",
                            ),
                            _contact_link(
                                "Telegram community (dedicated topic)",
                                "https://t.me/+4ON9YyZF4SM0M2Nk",
                            ),
                            _contact_link(
                                "LinkedIn showcase",
                                "https://www.linkedin.com/showcase/138363945/",
                            ),
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "8px",
                            },
                        ),
                        style={
                            "padding": "16px",
                            "borderRadius": "16px",
                            "border": "1px solid rgba(196, 181, 253, 0.24)",
                            "background": "rgba(15, 23, 42, 0.54)",
                            "boxShadow": "0 14px 34px rgba(2, 6, 23, 0.18)",
                            "margin": "0 0 18px 0",
                        },
                    ),
                    rx.el.div(
                        rx.el.h2(
                            "What we want to build next",
                            style={
                                "color": "#1a1a2e",
                                "fontSize": "1.35rem",
                                "fontWeight": "900",
                                "margin": "0 0 8px 0",
                            },
                        ),
                        rx.el.p(
                            rx.fragment(
                                "Early version — ideas exceed funding and hands. Have a feature request? ",
                                rx.el.a(
                                    "Open a GitHub issue",
                                    href="https://github.com/longevity-genie/materialized-enhancements/issues",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    style=_a,
                                ),
                                ".",
                            ),
                            style={**_p_body, "marginBottom": "10px"},
                        ),
                        rx.el.ul(
                            _roadmap_item(
                                "A deeper enhancement knowledge base",
                                "more genes and variants, richer evidence, side effects, and clearer known-vs-speculated notes.",
                            ),
                            _roadmap_item(
                                "Plasmid generation for selected genes",
                                "design and export plasmids carrying the enhancement genes you chose.",
                            ),
                            _roadmap_item(
                                "A map of who is working on this",
                                "companies, clinics, and labs offering or developing gene therapies for each enhancement.",
                            ),
                            _roadmap_item(
                                "A printable human 3D body of your enhanced state",
                                "today Materialize grows an abstract crystal; later, a full figure that visibly "
                                "reflects the traits you chose.",
                            ),
                            _roadmap_item(
                                "More art and fabrication options",
                                "more generative models on the same biological engine, better prints, and wearables.",
                            ),
                            _roadmap_item(
                                "Exhibition and classroom mode",
                                "guided walkthroughs, translations, and offline builds for museums and festivals.",
                            ),
                            style={
                                "margin": "0 0 12px 0",
                                "paddingLeft": "20px",
                                "listStyle": "disc",
                            },
                        ),
                        rx.el.p(
                            "Donations, grants, sponsorships, in-kind support, and volunteers decide how much of "
                            "this list gets built. Funding a specific feature? Get in touch.",
                            style={**_p_body, "marginBottom": "12px"},
                        ),
                        rx.el.div(
                            _contact_link("Support us on Ko-fi", "https://ko-fi.com/liviazaharia"),
                            _contact_link("Email Anton about funding", "mailto:antonkulaga@gmail.com"),
                            _contact_link("Email Livia about funding", "mailto:liviazaharia2020@gmail.com"),
                            _contact_link(
                                "Request a feature on GitHub",
                                "https://github.com/longevity-genie/materialized-enhancements/issues",
                            ),
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "8px",
                            },
                        ),
                        style={
                            "padding": "16px",
                            "borderRadius": "16px",
                            "border": "1px solid rgba(196, 181, 253, 0.24)",
                            "background": "rgba(15, 23, 42, 0.54)",
                            "boxShadow": "0 14px 34px rgba(2, 6, 23, 0.18)",
                            "margin": "0 0 18px 0",
                        },
                    ),
                    class_name="me-about-main",
                ),
                rx.el.aside(
                    rx.el.div(
                        rx.el.div("How it works", style=_sidebar_title),
                        rx.el.img(
                            src="/images/HOW_IT_WORKS.jpg",
                            alt="Materialized Enhancements process: trait input, parametric geometry, STL output, and 3D fabrication.",
                            loading="lazy",
                            decoding="async",
                            style={
                                "width": "100%",
                                "height": "auto",
                                "display": "block",
                                "borderRadius": "8px",
                                "boxShadow": "0 4px 18px rgba(0, 0, 0, 0.18)",
                            },
                        ),
                        style=_sidebar_card,
                    ),
                    rx.el.div(
                        rx.el.div("Core team", style=_sidebar_title),
                        rx.el.div(
                            _team_member(
                                "Newton Winter",
                                "web app, RPG interface, geometry optimization, devops, biology, UI",
                                "/images/team/newton_winter.webp",
                                "Newton Winter",
                                "https://github.com/winternewt",
                            ),
                            _team_member(
                                "Anton Kulaga",
                                "concept, biology, knowledge base, UI design, generative video, 3D printing",
                                "/images/team/anton_kulaga.jpg",
                                "Anton Kulaga",
                                "https://github.com/antonkulaga",
                            ),
                            _team_member(
                                "Livia Zaharia",
                                "parametric geometry, personalized enhancement report, 3D printing",
                                "/images/team/livia_zaharia.jpg",
                                "Livia Zaharia",
                                "http://livia.glucosedao.org/",
                            ),
                            style=_team_grid,
                        ),
                        style=_sidebar_card,
                    ),
                    rx.el.div(
                        rx.el.div("Contributors", style=_sidebar_title),
                        rx.el.div(
                            _team_member(
                                "Marko Prakhov-Donets",
                                "video editing",
                                "/images/team/markel.webp",
                                "Marko Prakhov-Donets",
                                "https://linktr.ee/markelkori",
                            ),
                            _team_member(
                                "Laura Radulescu",
                                "UI fixes, fast gene removal, materialize pop-ups",
                                link_href="https://github.com/LauraR20",
                            ),
                            style=_team_grid,
                        ),
                        style=_sidebar_card,
                    ),
                    rx.el.div(
                        rx.el.div("Support the project", style=_sidebar_title),
                        rx.el.div(
                            rx.el.a(
                                rx.el.img(
                                    src="/images/kofi.jpg",
                                    alt="Ko-fi QR code — support Materialized Enhancements",
                                    loading="lazy",
                                    decoding="async",
                                    style=_qr_image,
                                ),
                                rx.el.strong(
                                    "Buy us a coffee",
                                    style={
                                        "display": "block",
                                        "fontWeight": "700",
                                        "color": "#f8fafc",
                                        "fontSize": "0.95rem",
                                        "margin": "0 0 4px 0",
                                        "textAlign": "center",
                                    },
                                ),
                                rx.el.div(
                                    "Support the artists on Ko-fi",
                                    style={"color": "#cbd5e1", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                                ),
                                rx.el.div(
                                    "https://ko-fi.com/liviazaharia",
                                    style={
                                        "color": "#c4b5fd",
                                        "fontSize": "0.78rem",
                                        "margin": "6px 0 0 0",
                                        "textAlign": "center",
                                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                                        "wordBreak": "break-all",
                                    },
                                ),
                                href="https://ko-fi.com/liviazaharia",
                                target="_blank",
                                rel="noopener noreferrer",
                                style=_qr_card,
                            ),
                            rx.el.div(
                                rx.el.img(
                                    src="/images/product.jpg",
                                    alt="Product QR code — order your 3D-printed sculpture with delivery",
                                    loading="lazy",
                                    decoding="async",
                                    style=_qr_image,
                                ),
                                rx.el.strong(
                                    "Order your sculpture",
                                    style={
                                        "display": "block",
                                        "fontWeight": "700",
                                        "color": "#f8fafc",
                                        "fontSize": "0.95rem",
                                        "margin": "0 0 4px 0",
                                        "textAlign": "center",
                                    },
                                ),
                                rx.el.div(
                                    "3D-printed sculpture + delivery",
                                    style={"color": "#cbd5e1", "fontSize": "0.82rem", "margin": "0", "textAlign": "center"},
                                ),
                                style=_qr_card,
                            ),
                            class_name="me-about-support-grid",
                        ),
                        style=_sidebar_card,
                    ),
                    class_name="me-about-sidebar",
                ),
                class_name="me-about-layout",
            ),
            rx.el.p(
                "The stack is open source and meant to be extended: we invite other artists to plug their "
                "own generative models into the same biological input engine, and we welcome scientists to "
                "contribute to the gene list with new papers, new targets, or clearer annotations. "
                "The current list is not meant to be complete, so corrections and missing genes are welcome as "
                "GitHub issues. ",
                rx.el.a(
                    "Browse the repository on GitHub",
                    href="https://github.com/longevity-genie/materialized-enhancements",
                    target="_blank",
                    rel="noopener noreferrer",
                    style=_a,
                ),
                " or ",
                rx.el.a(
                    "open an issue",
                    href="https://github.com/longevity-genie/materialized-enhancements/issues",
                    target="_blank",
                    rel="noopener noreferrer",
                    style=_a,
                ),
                ".",
                style={**_p_body, "marginTop": "8px", "marginBottom": "0"},
            ),
            style={**_CONTENT_STYLE, "width": "100%", "maxWidth": "100%", "padding": "0 0.75rem"},
        ),
    )


# ── Tab 1: Materialize genetic enhancement (parametric form + report) ───────────


def _category_button(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    tooltip = _category_tooltip(category)
    total_count = GAME_CATEGORY_COUNTS.get(category, 0)
    total_price = CATEGORY_PRICES.get(category, 0)
    active_count = ComposeState.active_gene_counts[category]
    active_price = ComposeState.active_category_prices[category]
    is_selected = ComposeState.selected_categories.contains(category)
    is_affordable = ComposeState.affordable_categories.contains(category)
    is_enabled = is_selected | is_affordable

    return rx.el.div(
        rx.el.div(
            fomantic_icon(
                icon_name, size=18,
                color=rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, color, "#d1d5db")),
            ),
            rx.el.span(
                category,
                style={"fontSize": "1.02rem", "flex": "1", "marginLeft": "8px", "fontWeight": "600"},
            ),
            rx.el.span(
                rx.cond(
                    active_price == total_price,
                    f"{total_price} cr",
                    rx.cond(is_selected, active_price.to(str) + f"/{total_price} cr", f"{total_price} cr"),
                ),
                style={
                    "fontSize": "0.88rem",
                    "fontWeight": "700",
                    "padding": "2px 6px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#7c3aed", "#d1d5db")),
                    "marginRight": "4px",
                },
            ),
            rx.el.span(
                rx.cond(
                    active_count == total_count,
                    f"{total_count}",
                    rx.cond(is_selected, active_count.to(str) + f"/{total_count}", f"{total_count}"),
                ),
                style={
                    "fontSize": "0.88rem",
                    "fontWeight": "600",
                    "padding": "2px 7px",
                    "borderRadius": "10px",
                    "backgroundColor": rx.cond(is_selected, "rgba(255,255,255,0.25)", "#f3f4f6"),
                    "color": rx.cond(is_selected, "#ffffff", "#6b7280"),
                },
            ),
            style={"display": "flex", "alignItems": "center", "width": "100%"},
        ),
        on_click=ComposeState.select_category(category),
        title=tooltip,
        aria_label=tooltip,
        style={
            "marginBottom": "6px",
            "textAlign": "left",
            "cursor": rx.cond(is_enabled, "pointer", "not-allowed"),
            "padding": "11px 14px",
            "borderRadius": "6px",
            "border": "1px solid",
            "borderColor": rx.cond(is_selected, color, rx.cond(is_enabled, "#e5e7eb", "#f3f4f6")),
            "backgroundColor": rx.cond(is_selected, color, "#ffffff"),
            "color": rx.cond(is_selected, "#ffffff", rx.cond(is_enabled, "#1a1a2e", "#d1d5db")),
            "opacity": rx.cond(is_enabled, "1", "0.5"),
            "transition": "background-color 0.15s ease, border-color 0.15s ease, opacity 0.15s ease",
        },
    )


def _orientation_block() -> rx.Component:
    """Always-open first-screen brief: method, one reversal, takeaway, Show me how."""
    return rx.cond(
        ComposeState.show_mission_brief,
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    fomantic_icon("times", size=12, color="#94a3b8"),
                    on_click=ComposeState.dismiss_mission_brief,
                    title="Hide this brief",
                    aria_label="Hide this brief",
                    style={
                        "cursor": "pointer",
                        "opacity": "0.65",
                        "padding": "6px",
                        "borderRadius": "6px",
                        "marginLeft": "auto",
                    },
                    _hover={"opacity": "1"},
                ),
                style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "2px",
                },
            ),
            rx.el.p(
                "A game. A gene therapy knowledgebase. A bioart project.",
                class_name="me-orientation-headline",
            ),
            rx.el.p(
                f"Pick real genes from real animals and design an enhanced human. "
                f"{DEFAULT_BUDGET} credits, 80 genes from 71 species, and you cannot afford them all.",
                class_name="me-orientation-body",
            ),
            rx.el.p(
                "Tardigrade radiation shielding, naked mole-rat cancer resistance, axolotl limb regrowth. "
                "Each gene carries a rating for how far the evidence actually got: "
                "cells, animals, primates, human trials, on the market. "
                "You will know the trade-offs before you spend. "
                "Dsup, for example, shields human kidney cells "
                "from radiation but killed rat neurons outright.",
                class_name="me-orientation-body",
            ),
            rx.el.p(
                "Your gene choices grow a unique 3D-printable Voronoi crystal "
                "from the biophysical properties of those genes. "
                "Wear it, display it, or share the build.",
                class_name="me-orientation-body",
            ),
            rx.el.button(
                fomantic_icon("info circle", size=16, color="#f8fafc"),
                rx.el.span("Show me how", style={"marginLeft": "8px"}),
                type="button",
                on_click=ComposeState.start_onboarding,
                class_name="me-orientation-help",
            ),
            rx.el.p(
                "Just want to read about the genes? ",
                rx.el.a(
                    "Open the Knowledgebase",
                    href="/knowledgebase",
                    style={
                        "color": "#c4b5fd",
                        "fontWeight": "700",
                        "textDecoration": "underline",
                        "textUnderlineOffset": "2px",
                    },
                ),
                ".",
                class_name="me-orientation-kb",
            ),
            class_name="me-orientation-block",
        ),
        rx.fragment(),
    )


def _budget_gauge() -> rx.Component:
    """Sticky credit budget gauge."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                fomantic_icon("bolt", size=16, style={"color": ComposeState.budget_spent_color, "transition": "color 0.35s ease"}),
                rx.el.span(
                    "ENHANCEMENT CREDITS USED",
                    style={
                        "fontSize": "0.72rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.12em",
                        "color": ComposeState.budget_spent_color,
                        "transition": "color 0.35s ease",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "gap": "6px"},
            ),
            rx.el.div(
                rx.el.span(
                    ComposeState.budget_spent,
                    style={
                        "fontSize": "1.55rem",
                        "fontWeight": "950",
                        "color": ComposeState.budget_spent_color,
                        "lineHeight": "1",
                        "transition": "color 0.35s ease",
                    },
                ),
                rx.el.span(
                    f" / {DEFAULT_BUDGET} cr",
                    style={
                        "fontSize": "1.0rem",
                        "fontWeight": "700",
                        "color": "#64748b",
                        "lineHeight": "1",
                    },
                ),
                style={"display": "flex", "alignItems": "baseline", "gap": "2px"},
            ),
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "6px",
            },
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "6px",
                    "backgroundColor": ComposeState.budget_color,
                    "width": f"{ComposeState.budget_pct}%",
                    "transition": "width 0.35s cubic-bezier(.4,0,.2,1), background-color 0.35s ease",
                    "boxShadow": rx.cond(
                        ComposeState.budget_pct > 0,
                        f"0 0 12px {ComposeState.budget_color}66",
                        "none",
                    ),
                },
            ),
            style={
                "height": "10px",
                "borderRadius": "6px",
                "backgroundColor": "rgba(51, 65, 85, 0.5)",
                "overflow": "hidden",
            },
        ),
        rx.el.div(
            rx.el.span(
                ComposeState.budget_remaining,
                style={"fontWeight": "900", "color": ComposeState.budget_color},
            ),
            " cr remaining",
            style={
                "fontSize": "0.82rem",
                "fontWeight": "700",
                "color": "#64748b",
                "textAlign": "right",
                "marginTop": "4px",
            },
        ),
        class_name="me-budget-gauge",
    )


def _mobile_materialize_after_budget() -> rx.Component:
    """Mobile-only Materialize CTA that follows the sticky credit gauge."""
    return rx.el.div(
        _rpg_materialization_leg_cta(),
        class_name=rx.cond(
            ComposeState.show_onboarding_suggestion,
            "me-mobile-budget-materialize me-mobile-budget-materialize--hidden",
            "me-mobile-budget-materialize",
        ),
    )


def _mobile_budget_materialize_stack() -> rx.Component:
    """Budget gauge plus the mobile Materialize CTA in one sticky mobile stack."""
    return rx.el.div(
        _budget_gauge(),
        _mobile_materialize_after_budget(),
        class_name="me-mobile-budget-stack",
    )


def _sculpture_how_it_works_callout() -> rx.Component:
    """Full-width explainer above credits, category pick, and Choice: cr → 3D model + report."""
    return rx.el.div(
        rx.el.p(
            "Spend enhancement credits (cr) to choose the genetic enhancement areas you want. "
            "Pick categories (left sidebar), select genes (on the right), and push materialize (on the bottom). "
            "You will get a printable crystal grown from your choices — an abstract form, not a body figure yet — "
            "plus a report you can share with friends.",
            style={
                "fontSize": "0.88rem",
                "lineHeight": "1.5",
                "color": "#4b5563",
                "margin": "0",
            },
        ),
        style={
            "width": "100%",
            "boxSizing": "border-box",
            "padding": "10px 12px",
            "borderRadius": "6px",
            "backgroundColor": "#f0f9ff",
            "border": "1px solid #bae6fd",
            "marginBottom": "12px",
        },
    )


def _sculpture_left_pane() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("dna", size=18, color="#7c3aed"),
            rx.el.span(" Choose Categories", style={"marginLeft": "8px"}),
            style={
                "color": "#1a1a2e",
                "marginBottom": "12px",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "1.12rem",
                "fontWeight": "700",
            },
        ),
        _budget_gauge(),
        rx.el.div(
            *[_category_button(cat) for cat in UNIQUE_CATEGORIES],
        ),
        rx.el.div(
            rx.el.div(class_name="ui divider"),
            rx.el.p(
                f"{len(GENE_LIBRARY)} genes · {len(UNIQUE_CATEGORIES)} categories",
                style={"fontSize": "0.78rem", "color": "#9ca3af", "textAlign": "center"},
            ),
            rx.el.p(
                "Each combination grows a one-of-a-kind printable crystal — "
                "an abstract form from your gene choices, printable in resin, ceramic, or metal.",
                style={
                    "fontSize": "0.78rem",
                    "color": "#9ca3af",
                    "textAlign": "center",
                    "marginTop": "8px",
                    "lineHeight": "1.45",
                },
            ),
            style={"marginTop": "16px"},
        ),
    )


def _selected_category_tag(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        rx.el.span(cat_item, style={"marginRight": "6px"}),
        rx.el.span(
            fomantic_icon("times", size=10),
            on_click=ComposeState.remove_category(cat_item),
            style={"cursor": "pointer", "opacity": "0.7"},
        ),
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "padding": "4px 10px",
            "borderRadius": "16px",
            "backgroundColor": "#f3f0ff",
            "color": "#7c3aed",
            "fontSize": "0.95rem",
            "fontWeight": "500",
            "margin": "3px",
            "border": "1px solid #d4c5f9",
        },
    )


def _trait_item(trait: rx.Var) -> rx.Component:
    return rx.el.div(
        fomantic_icon("check", size=10, color="#7c3aed"),
        rx.el.span(trait, style={"marginLeft": "6px", "fontSize": "0.88rem", "color": "#374151"}),
        style={"display": "flex", "alignItems": "center", "padding": "4px 0"},
    )


def _gene_selection_text_block(title: str, segments: rx.Var) -> rx.Component:
    return rx.cond(
        segments.length() > 0,
        rx.el.div(
            rx.el.div(
                title,
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "900",
                    "color": "#a5b4fc",
                    "marginBottom": "4px",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                },
            ),
            rx.el.p(
                rx.foreach(segments, _gene_prose_segment),
                style={
                    "fontSize": "0.96rem",
                    "color": "#dbeafe",
                    "margin": "0 0 12px 0",
                    "lineHeight": "1.6",
                    "whiteSpace": "pre-wrap",
                },
            ),
        ),
        rx.fragment(),
    )


def _gene_selection_prop_row(label: str, value: rx.Var) -> rx.Component:
    return rx.cond(
        value != "",
        rx.el.div(
            rx.el.span(label, style={"fontSize": "0.93rem", "color": "#6b7280", "flex": "1 1 55%"}),
            rx.el.span(value, style={"fontSize": "0.93rem", "color": "#374151", "fontWeight": "500", "textAlign": "right"}),
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "gap": "8px",
                "padding": "3px 0",
                "borderBottom": "1px solid #f3f4f6",
            },
        ),
        rx.fragment(),
    )


_CONF_PILL_STYLES: dict[str, dict[str, str]] = {
    "very high": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#d1fae7",
        "color": "#047857", "border": "1px solid #6ee7b7",
        "whiteSpace": "nowrap",
    },
    "high": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#d1fae7",
        "color": "#047857", "border": "1px solid #6ee7b7",
        "whiteSpace": "nowrap",
    },
    "medium-high": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#cffafe",
        "color": "#0e7490", "border": "1px solid #67e8f9",
        "whiteSpace": "nowrap",
    },
    "medium": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#fef3c7",
        "color": "#b45309", "border": "1px solid #fcd34d",
        "whiteSpace": "nowrap",
    },
    "medium-low": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#fee2e2",
        "color": "#b91c1c", "border": "1px solid #fecaca",
        "whiteSpace": "nowrap",
    },
    "low-medium": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#fee2e2",
        "color": "#b91c1c", "border": "1px solid #fecaca",
        "whiteSpace": "nowrap",
    },
    "low": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#fee2e2",
        "color": "#b91c1c", "border": "1px solid #fecaca",
        "whiteSpace": "nowrap",
    },
    "declining": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#fee2e2",
        "color": "#b91c1c", "border": "1px solid #fecaca",
        "whiteSpace": "nowrap",
    },
    "n/a": {
        "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
        "borderRadius": "6px", "backgroundColor": "#f3f4f6",
        "color": "#4b5563", "border": "1px solid #e5e7eb",
        "whiteSpace": "nowrap",
    },
}

_CONF_PILL_DEFAULT = {
    "fontSize": "0.82rem", "fontWeight": "600", "padding": "2px 10px",
    "borderRadius": "6px", "backgroundColor": "#f3f4f6",
    "color": "#4b5563", "border": "1px solid #e5e7eb",
    "whiteSpace": "nowrap",
}


def _confidence_detail_line(entry: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            entry["value"],
            style={
                "fontSize": "0.78rem",
                "fontWeight": "600",
                "color": "#94a3b8",
            },
        ),
        rx.cond(
            entry["argument"] != "",
            rx.el.span(
                entry["argument"],
                style={"fontSize": "0.78rem", "color": "#cbd5e1", "marginLeft": "4px"},
            ),
            rx.fragment(),
        ),
        rx.cond(
            entry["description"] != "",
            rx.el.span(
                " — ",
                rx.el.span(entry["description"], style={"fontStyle": "italic"}),
                style={"fontSize": "0.74rem", "color": "#64748b", "marginLeft": "2px"},
            ),
            rx.fragment(),
        ),
        style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px", "padding": "1px 0"},
    )


def _gene_confidence_section(
    primary: rx.Var,
    details: rx.Var | None = None,
    show_details: bool = False,
) -> rx.Component:
    """Show the mammal/human-facing primary confidence pill.

    Secondary rows (biomaterial, source-organism, biochem) stay out of the
    game card by default — pass show_details=True only in expanded/report views.
    """
    val_lower = primary["value"].lower()
    pill = rx.el.span(
        primary["value"],
        style=rx.match(
            val_lower,
            *[(k, v) for k, v in _CONF_PILL_STYLES.items()],
            _CONF_PILL_DEFAULT,
        ),
    )
    primary_arg = rx.cond(
        primary["argument"] != "",
        rx.el.span(
            primary["argument"],
            style={"fontSize": "0.82rem", "color": "#e2e8f0", "marginLeft": "6px"},
        ),
        rx.fragment(),
    )
    primary_desc = rx.cond(
        primary["description"] != "",
        rx.el.span(
            " — ",
            rx.el.span(primary["description"], style={"fontStyle": "italic"}),
            style={"fontSize": "0.78rem", "color": "#94a3b8", "marginLeft": "2px"},
        ),
        rx.fragment(),
    )
    detail_block = (
        rx.cond(
            details.length() > 0,
            rx.el.div(
                rx.foreach(details, _confidence_detail_line),
                style={"marginLeft": "8px", "marginTop": "2px"},
            ),
            rx.fragment(),
        )
        if show_details and details is not None
        else rx.fragment()
    )
    return rx.cond(
        primary["value"] != "",
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Confidence",
                    style={
                        "fontSize": "0.95rem",
                        "fontWeight": "900",
                        "color": "#94a3b8",
                        "marginRight": "8px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.06em",
                    },
                ),
                pill,
                primary_arg,
                primary_desc,
                style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px"},
            ),
            detail_block,
            style={"display": "flex", "flexDirection": "column", "gap": "2px"},
        ),
        rx.fragment(),
    )


def _tested_host_badge(entry: rx.Var) -> rx.Component:
    return rx.el.span(
        _testing_positive_dot(entry["positive"]),
        entry["host"],
        rx.cond(
            entry["tissue_or_system"] != "",
            rx.el.span(
                " (", entry["tissue_or_system"], ")",
                style={"color": "#94a3b8", "fontSize": "0.68rem"},
            ),
            rx.fragment(),
        ),
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "2px",
            "fontSize": "0.76rem",
            "color": "#cbd5e1",
            "background": "rgba(148,163,184,0.1)",
            "borderRadius": "4px",
            "padding": "1px 6px",
            "whiteSpace": "nowrap",
        },
    )


def _gene_tested_on_row(testing_entries: rx.Var) -> rx.Component:
    return rx.cond(
        testing_entries.length() > 0,
        rx.el.div(
            rx.el.span(
                "Tested on",
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "flexShrink": "0",
                },
            ),
            rx.foreach(testing_entries, _tested_host_badge),
            style={"display": "flex", "alignItems": "center", "gap": "4px", "flexWrap": "wrap"},
        ),
        rx.fragment(),
    )


def _gene_tested_on_fold(testing_entries: rx.Var) -> rx.Component:
    """Collapsed host list — can be long, so keep it behind a details toggle."""
    return rx.cond(
        testing_entries.length() > 0,
        rx.el.details(
            rx.el.summary(
                rx.el.span(
                    "Tested on",
                    style={
                        "fontSize": "0.9rem",
                        "fontWeight": "900",
                        "color": "#94a3b8",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.06em",
                    },
                ),
                rx.el.span(
                    "(",
                    testing_entries.length().to(str),
                    ")",
                    style={
                        "fontSize": "0.78rem",
                        "fontWeight": "700",
                        "color": "#64748b",
                        "marginLeft": "6px",
                    },
                ),
                style={
                    "cursor": "pointer",
                    "display": "flex",
                    "alignItems": "center",
                    "listStyle": "none",
                    "padding": "8px 10px",
                    "borderRadius": "7px",
                    "background": "rgba(148, 163, 184, 0.08)",
                    "border": "1px solid rgba(148, 163, 184, 0.22)",
                    "color": "#cbd5e1",
                    "userSelect": "none",
                },
            ),
            rx.el.div(
                rx.foreach(testing_entries, _tested_host_badge),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "4px",
                    "flexWrap": "wrap",
                    "padding": "10px 4px 2px 4px",
                },
            ),
            class_name="me-gene-tested-on-fold",
            style={"margin": "4px 0"},
        ),
        rx.fragment(),
    )


def _gene_evidence_tier_row(evidence_tier: rx.Var) -> rx.Component:
    """Compact highest-evidence-tier label for the default gene-card surface."""
    return rx.cond(
        evidence_tier != "",
        rx.el.div(
            rx.el.span(
                "Highest evidence",
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "flexShrink": "0",
                },
            ),
            rx.el.span(
                evidence_tier,
                style={
                    "fontSize": "0.82rem",
                    "fontWeight": "700",
                    "padding": "2px 10px",
                    "borderRadius": "6px",
                    "backgroundColor": "rgba(56, 189, 248, 0.14)",
                    "color": "#7dd3fc",
                    "border": "1px solid rgba(125, 211, 252, 0.35)",
                    "whiteSpace": "nowrap",
                },
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px"},
        ),
        rx.fragment(),
    )


def _availability_badge(label: str, background: str, color: str, border: str) -> rx.Component:
    return rx.el.span(
        label,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "fontSize": "0.76rem",
            "fontWeight": "800",
            "lineHeight": "1.15",
            "padding": "4px 10px",
            "borderRadius": "999px",
            "backgroundColor": background,
            "color": color,
            "border": border,
            "letterSpacing": "0.04em",
            "textTransform": "uppercase",
            "whiteSpace": "nowrap",
            "boxSizing": "border-box",
        },
    )


def _gene_availability_badges(gene_item: rx.Var) -> rx.Component:
    """Show commercial / clinical-trial status above Details when present."""
    return rx.cond(
        gene_item["has_commercial"] | gene_item["has_clinical_trial"],
        rx.el.div(
            rx.el.span(
                "Status",
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
                    "marginRight": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "flexShrink": "0",
                },
            ),
            rx.cond(
                gene_item["has_commercial"],
                _availability_badge(
                    "Commercial",
                    "rgba(52, 211, 153, 0.16)",
                    "#6ee7b7",
                    "1px solid rgba(110, 231, 183, 0.4)",
                ),
                rx.fragment(),
            ),
            rx.cond(
                gene_item["has_clinical_trial"],
                _availability_badge(
                    "Clinical trial",
                    "rgba(96, 165, 250, 0.16)",
                    "#93c5fd",
                    "1px solid rgba(147, 197, 253, 0.4)",
                ),
                rx.fragment(),
            ),
            style={"display": "flex", "alignItems": "center", "gap": "6px", "flexWrap": "wrap"},
        ),
        rx.fragment(),
    )


_POSITIVE_COLORS: dict[str, str] = {
    "true": "#22c55e",
    "false": "#ef4444",
    "mixed": "#f59e0b",
}


def _testing_positive_dot(val: rx.Var) -> rx.Component:
    return rx.el.span(
        "●",
        style={
            "color": rx.cond(
                val == "true",
                "#22c55e",
                rx.cond(val == "false", "#ef4444", "#f59e0b"),
            ),
            "fontSize": "0.7rem",
            "marginRight": "2px",
        },
    )


def _testing_entry_row(entry: rx.Var) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            _testing_positive_dot(entry["positive"]),
            rx.el.span(entry["host"], style={"fontWeight": "600"}),
            style={"padding": "3px 8px 3px 4px", "whiteSpace": "nowrap"},
        ),
        rx.el.td(
            entry["tissue_or_system"],
            style={"padding": "3px 8px", "color": "#94a3b8"},
        ),
        rx.el.td(
            entry["intervention"],
            style={"padding": "3px 8px"},
        ),
        rx.el.td(
            entry["delivery"],
            style={"padding": "3px 8px", "color": "#94a3b8"},
        ),
        rx.el.td(
            entry["integration"],
            style={"padding": "3px 8px", "color": "#94a3b8"},
        ),
        rx.el.td(
            entry["key_result"],
            style={"padding": "3px 8px", "maxWidth": "320px"},
        ),
        rx.el.td(
            rx.cond(
                entry["doi"] != "",
                rx.el.a(
                    entry["reference_short"],
                    href=entry["doi"],
                    target="_blank",
                    rel="noopener noreferrer",
                    style={"color": "#93c5fd", "textDecoration": "underline", "textUnderlineOffset": "2px"},
                ),
                rx.el.span(entry["reference_short"]),
            ),
            style={"padding": "3px 8px", "whiteSpace": "nowrap"},
        ),
        style={"borderBottom": "1px solid rgba(148,163,184,0.1)"},
    )


def _gene_testing_records(testing_entries: rx.Var) -> rx.Component:
    """Render testing records inside an already-collapsed parent section."""
    return rx.cond(
        testing_entries.length() > 0,
        rx.el.div(
            rx.el.div(
                "Testing records (",
                testing_entries.length().to(str),
                ")",
                style={
                    "fontSize": "0.9rem",
                    "fontWeight": "900",
                    "color": "#94a3b8",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Host", style={"padding": "4px 8px 4px 4px", "textAlign": "left"}),
                            rx.el.th("System", style={"padding": "4px 8px", "textAlign": "left"}),
                            rx.el.th("Intervention", style={"padding": "4px 8px", "textAlign": "left"}),
                            rx.el.th("Delivery", style={"padding": "4px 8px", "textAlign": "left"}),
                            rx.el.th("Integration", style={"padding": "4px 8px", "textAlign": "left"}),
                            rx.el.th("Key Result", style={"padding": "4px 8px", "textAlign": "left"}),
                            rx.el.th("Reference", style={"padding": "4px 8px", "textAlign": "left"}),
                            style={
                                "fontSize": "0.7rem",
                                "fontWeight": "700",
                                "color": "#64748b",
                                "textTransform": "uppercase",
                                "letterSpacing": "0.05em",
                                "borderBottom": "1px solid rgba(148,163,184,0.2)",
                            },
                        ),
                    ),
                    rx.el.tbody(
                        rx.foreach(testing_entries, _testing_entry_row),
                    ),
                    style={
                        "width": "100%",
                        "fontSize": "0.76rem",
                        "color": "#cbd5e1",
                        "borderCollapse": "collapse",
                    },
                ),
                style={
                    "overflowX": "auto",
                    "maxWidth": "100%",
                    "padding": "10px 4px 2px 4px",
                },
            ),
            style={"margin": "8px 0"},
        ),
        rx.fragment(),
    )


def _gene_testing_table(testing_entries: rx.Var) -> rx.Component:
    """Collapsed testing table used in long-form report rows."""
    return rx.cond(
        testing_entries.length() > 0,
        rx.el.details(
            rx.el.summary(
                rx.el.span(
                    "Testing evidence",
                    style={
                        "fontSize": "0.9rem",
                        "fontWeight": "900",
                        "color": "#94a3b8",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.06em",
                    },
                ),
                style={
                    "cursor": "pointer",
                    "listStyle": "none",
                    "padding": "8px 10px",
                    "borderRadius": "7px",
                    "background": "rgba(148, 163, 184, 0.08)",
                    "border": "1px solid rgba(148, 163, 184, 0.22)",
                },
            ),
            _gene_testing_records(testing_entries),
            class_name="me-gene-testing-evidence-fold",
        ),
        rx.fragment(),
    )


def _org_type_label(org_type: rx.Var) -> rx.Component:
    return rx.match(
        org_type,
        ("biotech_company", rx.el.span("Company", style={"color": "#34d399", "fontWeight": "700", "fontSize": "0.68rem", "textTransform": "uppercase"})),
        ("clinic", rx.el.span("Clinic", style={"color": "#fbbf24", "fontWeight": "700", "fontSize": "0.68rem", "textTransform": "uppercase"})),
        ("clinical_trial_sponsor", rx.el.span("Trial sponsor", style={"color": "#60a5fa", "fontWeight": "700", "fontSize": "0.68rem", "textTransform": "uppercase"})),
        ("academic_lab", rx.el.span("Lab", style={"color": "#94a3b8", "fontWeight": "700", "fontSize": "0.68rem", "textTransform": "uppercase"})),
        rx.el.span(org_type, style={"fontSize": "0.68rem", "color": "#94a3b8"}),
    )


def _org_entry_row(entry: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _org_type_label(entry["org_type"]),
            rx.cond(
                entry["website"] != "",
                rx.el.a(
                    entry["org_name"],
                    href=entry["website"],
                    target="_blank",
                    style={"color": "#c4b5fd", "fontWeight": "600", "fontSize": "0.82rem", "marginLeft": "6px", "textDecoration": "none"},
                ),
                rx.el.span(entry["org_name"], style={"fontWeight": "600", "fontSize": "0.82rem", "marginLeft": "6px", "color": "#e2e8f0"}),
            ),
            style={"display": "flex", "alignItems": "center", "gap": "2px", "flexWrap": "wrap"},
        ),
        rx.el.div(
            rx.el.span(
                entry["stage"],
                style={
                    "display": "inline-block",
                    "padding": "1px 6px",
                    "background": "rgba(124, 58, 237, 0.18)",
                    "border": "1px solid rgba(196, 181, 253, 0.3)",
                    "borderRadius": "8px",
                    "color": "#c4b5fd",
                    "fontSize": "0.7rem",
                    "fontWeight": "600",
                },
            ),
            rx.cond(
                entry["delivery_method"] != "",
                rx.el.span(entry["delivery_method"], style={"fontSize": "0.76rem", "color": "#94a3b8", "marginLeft": "6px"}),
                rx.fragment(),
            ),
            rx.cond(
                entry["price_usd"] != "",
                rx.el.span(
                    entry["price_usd"],
                    style={"fontSize": "0.78rem", "color": "#34d399", "fontWeight": "700", "marginLeft": "8px"},
                ),
                rx.fragment(),
            ),
            rx.cond(
                entry["trial_id"] != "",
                rx.el.a(
                    entry["trial_id"],
                    href=rx.cond(
                        entry["trial_id"].contains("NCT"),
                        "https://clinicaltrials.gov/study/" + entry["trial_id"],
                        "#",
                    ),
                    target="_blank",
                    style={"fontSize": "0.72rem", "color": "#60a5fa", "marginLeft": "8px"},
                ),
                rx.fragment(),
            ),
            style={"display": "flex", "alignItems": "center", "gap": "4px", "flexWrap": "wrap", "marginTop": "2px"},
        ),
        rx.cond(
            entry["evidence_summary"] != "",
            rx.el.p(
                entry["evidence_summary"],
                style={"fontSize": "0.76rem", "color": "#cbd5e1", "margin": "2px 0 0 0", "lineHeight": "1.4"},
            ),
            rx.fragment(),
        ),
        rx.cond(
            entry["source_url"] != "",
            rx.el.a(
                fomantic_icon("external-link", size=9, color="#94a3b8"),
                " source",
                href=entry["source_url"],
                target="_blank",
                style={"fontSize": "0.68rem", "color": "#94a3b8", "textDecoration": "none", "display": "inline-flex", "alignItems": "center", "gap": "2px", "marginTop": "2px"},
            ),
            rx.fragment(),
        ),
        style={
            "padding": "8px 12px",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.15)",
        },
    )


def _gene_organizations_section(org_entries: rx.Var) -> rx.Component:
    return rx.cond(
        org_entries.length() > 0,
        rx.el.div(
            rx.el.div(
                fomantic_icon("building", size=12, color="#94a3b8"),
                rx.el.span(
                    " Labs & Therapies",
                    style={"marginLeft": "4px"},
                ),
                style={
                    "fontSize": "0.82rem",
                    "fontWeight": "800",
                    "color": "#94a3b8",
                    "margin": "8px 0 4px 0",
                    "display": "flex",
                    "alignItems": "center",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                },
            ),
            rx.el.div(
                rx.foreach(org_entries, _org_entry_row),
                style={
                    "border": "1px solid rgba(148, 163, 184, 0.2)",
                    "borderRadius": "6px",
                    "overflow": "hidden",
                    "background": "rgba(15, 23, 42, 0.3)",
                },
            ),
            style={"margin": "8px 0"},
        ),
        rx.fragment(),
    )


def _gene_prose_segment(seg: rx.Var) -> rx.Component:
    """Render one linkified prose chunk (text / link / paragraph break)."""
    return rx.match(
        seg["kind"],
        (
            "link",
            rx.el.a(
                seg["v"],
                href=seg["href"],
                target="_blank",
                rel="noopener noreferrer",
                style={
                    "color": "#93c5fd",
                    "textDecoration": "underline",
                    "textUnderlineOffset": "2px",
                    "wordBreak": "break-word",
                },
            ),
        ),
        (
            "para_break",
            rx.el.br(),
        ),
        rx.el.span(seg["v"]),
    )


def _gene_key_reference_segment(seg: rx.Var) -> rx.Component:
    return _gene_prose_segment(seg)


def _gene_key_references_linked(segments: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Key references",
            style={
                "fontSize": "0.82rem",
                "fontWeight": "600",
                "color": "#475569",
                "marginBottom": "4px",
                "letterSpacing": "0.02em",
            },
        ),
        rx.el.p(
            rx.foreach(segments, _gene_key_reference_segment),
            style={
                "fontSize": "0.8rem",
                "margin": "0 0 10px 0",
                "lineHeight": "1.55",
                "whiteSpace": "pre-wrap",
            },
        ),
    )


def _gene_category_border_left(category: rx.Var) -> rx.Var:
    """Thin left accent matching sidebar category color (parent `category` key)."""
    return rx.match(
        category,
        ("Stress Resistance", "2px solid #e67e22"),
        ("Longevity & Genome", "2px solid #27ae60"),
        ("Regeneration", "2px solid #16a085"),
        ("Environmental Adaptation", "2px solid #2980b9"),
        ("Perception", "2px solid #e84393"),
        ("Expression", "2px solid #8e44ad"),
        "2px solid #cbd5e1",
    )


def _gene_category_accent_color(category: rx.Var) -> rx.Var:
    """Same hue as CATEGORY_COLORS / left border — for trait line in reports."""
    return rx.match(
        category,
        ("Stress Resistance", "#e67e22"),
        ("Longevity & Genome", "#27ae60"),
        ("Regeneration", "#16a085"),
        ("Environmental Adaptation", "#2980b9"),
        ("Perception", "#e84393"),
        ("Expression", "#8e44ad"),
        "#7c3aed",
    )


def _confidence_bar_count(confidence_value: rx.Var) -> rx.Var:
    """Map confidence tier to number of lit bars (0–4)."""
    val_lower = confidence_value.lower()
    return rx.match(
        val_lower,
        ("very high", 4),
        ("high", 3),
        ("medium-high", 3),
        ("medium", 2),
        ("medium-low", 1),
        ("low-medium", 1),
        ("low", 1),
        ("declining", 0),
        ("n/a", 0),
        0,
    )


def _confidence_bar_color(confidence_value: rx.Var) -> rx.Var:
    """Color for lit bars — green for strong, amber for mid, red for weak."""
    val_lower = confidence_value.lower()
    return rx.match(
        val_lower,
        ("very high", "#10b981"),
        ("high", "#10b981"),
        ("medium-high", "#0ea5e9"),
        ("medium", "#f59e0b"),
        ("medium-low", "#ef4444"),
        ("low-medium", "#ef4444"),
        ("low", "#ef4444"),
        ("declining", "#ef4444"),
        ("n/a", "#64748b"),
        "#64748b",
    )


def _confidence_signal_bars(confidence_value: rx.Var) -> rx.Component:
    """Compact 4-bar signal-strength indicator for confidence tier."""
    n_lit = _confidence_bar_count(confidence_value).to(int)
    color = _confidence_bar_color(confidence_value)
    dim = "rgba(148, 163, 184, 0.22)"

    def _bar(index: int) -> rx.Component:
        height = f"{5 + index * 3}px"
        return rx.el.div(
            style={
                "width": "3px",
                "height": height,
                "borderRadius": "1px",
                "backgroundColor": rx.cond(n_lit > index, color, dim),
                "transition": "background-color 0.2s ease",
            },
        )

    return rx.cond(
        confidence_value != "",
        rx.el.div(
            _bar(0),
            _bar(1),
            _bar(2),
            _bar(3),
            title=confidence_value,
            style={
                "display": "inline-flex",
                "alignItems": "flex-end",
                "gap": "2px",
                "marginLeft": "6px",
                "flexShrink": "0",
                "cursor": "default",
            },
        ),
        rx.fragment(),
    )


def _secondary_category_badge(cat_name: rx.Var) -> rx.Component:
    color = rx.match(
        cat_name,
        ("Stress Resistance", "#e67e22"),
        ("Longevity & Genome", "#27ae60"),
        ("Regeneration", "#16a085"),
        ("Environmental Adaptation", "#2980b9"),
        ("Perception", "#e84393"),
        ("Expression", "#8e44ad"),
        "#7c3aed",
    )
    icon_name = rx.match(
        cat_name,
        ("Stress Resistance", "shield"),
        ("Longevity & Genome", "heartbeat"),
        ("Regeneration", "sync"),
        ("Environmental Adaptation", "globe"),
        ("Perception", "eye"),
        ("Expression", "paint brush"),
        "star",
    )
    return rx.el.span(
        fomantic_icon(icon_name, size=10, color=color),
        cat_name,
        title=cat_name,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "4px",
            "fontSize": "0.7rem",
            "fontWeight": "700",
            "padding": "1px 7px",
            "borderRadius": "4px",
            "backgroundColor": f"color-mix(in srgb, {color} 18%, transparent)",
            "border": f"1px solid color-mix(in srgb, {color} 35%, transparent)",
            "color": color,
            "whiteSpace": "nowrap",
        },
    )


def _secondary_categories_row(gene_item: rx.Var) -> rx.Component:
    return rx.cond(
        gene_item["secondary_categories"].length() > 0,
        rx.el.div(
            rx.foreach(
                gene_item["secondary_categories"],
                _secondary_category_badge,
            ),
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "4px",
                "marginTop": "3px",
            },
        ),
        rx.fragment(),
    )


_MANIPULATION_ICON_MAP: list[tuple[str, str]] = [
    ("knockout", "cut"),
    ("knockin", "sign in"),
    ("overexpression", "level up alternate"),
    ("transfer", "exchange"),
    ("editing", "pencil alternate"),
    ("expansion", "copy"),
    ("expression", "plus circle"),
]


def _manipulation_icon(icon_key: rx.Var, size: int = 11, color: str = "#6d28d9") -> rx.Component:
    return rx.match(
        icon_key,
        *[(k, fomantic_icon(icon, size=size, color=color)) for k, icon in _MANIPULATION_ICON_MAP],
        fomantic_icon("dna", size=size, color=color),
    )


def _manipulation_badge(gene_item: rx.Var, included: rx.Var) -> rx.Component:
    return rx.el.span(
        _manipulation_icon(
            gene_item["manipulation_icon"],
            size=10,
            color=rx.cond(included, "#6d28d9", "#9ca3af"),
        ),
        gene_item["manipulation"],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "4px",
            "fontSize": "0.72rem",
            "fontWeight": "600",
            "padding": "1px 6px",
            "borderRadius": "4px",
            "backgroundColor": rx.cond(included, "#f3f0ff", "#f3f4f6"),
            "color": rx.cond(included, "#6d28d9", "#9ca3af"),
            "whiteSpace": "nowrap",
            "flexShrink": "0",
        },
    )


def _manipulation_badge_dark(gene_item: rx.Var) -> rx.Component:
    return rx.el.span(
        _manipulation_icon(gene_item["manipulation_icon"], size=10, color="#c4b5fd"),
        gene_item["manipulation"],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "4px",
            "fontSize": "0.72rem",
            "fontWeight": "700",
            "padding": "2px 8px",
            "borderRadius": "4px",
            "backgroundColor": "rgba(124, 58, 237, 0.16)",
            "color": "#c4b5fd",
            "whiteSpace": "nowrap",
        },
    )


def _gene_checkbox(gene_item: rx.Var) -> rx.Component:
    gene_sym = gene_item["gene"]
    included = ComposeState.included_genes.contains(gene_sym)
    gene_price = gene_item["price"].to(int)
    cannot_afford = rx.cond(included, False, gene_price > ComposeState.budget_remaining)
    # genes.game_enabled = 0: readable in the library, but not selectable yet
    # (its 3D-model inputs are not populated). Locked takes priority over price.
    locked = ~gene_item["playable"].to(bool)
    disabled = locked | cannot_afford

    return rx.el.div(
        # Header row: checkbox + labels + expand toggle
        rx.el.div(
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    checked=included,
                    disabled=disabled,
                    on_change=ComposeState.toggle_gene(gene_sym),
                    title=rx.cond(
                        locked,
                        "In the knowledge base only — not yet available to add",
                        "",
                    ),
                    style={
                        "marginRight": "6px",
                        "accentColor": "#7c3aed",
                        "cursor": rx.cond(disabled, "not-allowed", "pointer"),
                        "flexShrink": "0",
                        "opacity": rx.cond(disabled, "0.45", "1"),
                    },
                ),
                rx.el.span(
                    gene_sym,
                    style={
                        "fontSize": "0.93rem",
                        "fontWeight": "600",
                        "color": rx.cond(included, "#1a1a2e", "#9ca3af"),
                        "flexShrink": "0",
                    },
                ),
                _manipulation_badge(gene_item, included),
                rx.el.span(
                    gene_item["category_detail"],
                    style={
                        "fontSize": "0.88rem",
                        "fontWeight": "500",
                        "color": rx.cond(included, "#6b7280", "#d1d5db"),
                        "maxWidth": "28%",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                    },
                ),
                rx.cond(
                    gene_item["species_page_url"] != "",
                    rx.el.a(
                        gene_item["species_common_names"],
                        " ",
                        rx.el.span(
                            gene_item["species_scientific_names"],
                            style={"fontStyle": "italic", "opacity": "0.75"},
                        ),
                        href=gene_item["species_page_url"],
                        target="_blank",
                        rel="noopener noreferrer",
                        style={
                            "fontSize": "0.88rem",
                            "color": rx.cond(included, "#6b7280", "#9ca3af"),
                            "marginLeft": "6px",
                            "flex": "1",
                            "textAlign": "right",
                            "minWidth": "0",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                            "textDecoration": "none",
                            "_hover": {"textDecoration": "underline"},
                        },
                    ),
                    rx.el.span(
                        gene_item["species_common_names"],
                        " ",
                        rx.el.span(
                            gene_item["species_scientific_names"],
                            style={"fontStyle": "italic", "opacity": "0.75"},
                        ),
                        style={
                            "fontSize": "0.88rem",
                            "color": rx.cond(included, "#6b7280", "#9ca3af"),
                            "marginLeft": "6px",
                            "flex": "1",
                            "textAlign": "right",
                            "minWidth": "0",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ),
                rx.el.span(
                    gene_item["price"],
                    " cr",
                    style={
                        "fontSize": "0.86rem",
                        "fontWeight": "700",
                        "padding": "1px 6px",
                        "borderRadius": "10px",
                        "border": rx.cond(
                            included,
                            "1px solid transparent",
                            rx.cond(cannot_afford, "1px solid #fecaca", "1px solid transparent"),
                        ),
                        "backgroundColor": rx.cond(
                            included,
                            "#f3f0ff",
                            rx.cond(cannot_afford, "#fef2f2", "#f3f4f6"),
                        ),
                        "color": rx.cond(
                            included,
                            "#7c3aed",
                            rx.cond(cannot_afford, "#dc2626", "#d1d5db"),
                        ),
                        "whiteSpace": "nowrap",
                        "marginLeft": "6px",
                    },
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "flex": "1",
                    "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                    "padding": "5px 8px",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.el.p(
            rx.foreach(gene_item["short_description_segments"], _gene_prose_segment),
            style={
                "fontSize": "0.83rem",
                "color": "#374151",
                "margin": "4px 14px 4px 36px",
                "lineHeight": "1.55",
                "whiteSpace": "pre-wrap",
            },
        ),
        rx.el.div(
            _gene_confidence_section(gene_item["confidence_primary"]),
            _gene_evidence_tier_row(gene_item["evidence_tier"]),
            _gene_availability_badges(gene_item),
            _gene_ai_controls(gene_item, dark=False),
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "6px",
                "margin": "6px 14px 4px 36px",
            },
        ),
        rx.el.div(
            _gene_information_folds(gene_item, dark=False),
            style={"margin": "0 14px 10px 36px"},
        ),
        style={
            "borderRadius": "4px",
            "borderTop": "1px solid",
            "borderRight": "1px solid",
            "borderBottom": "1px solid",
            "borderTopColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderRightColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderBottomColor": rx.cond(included, "#e5e7eb", "#f3f4f6"),
            "borderLeft": rx.cond(
                included,
                _gene_category_border_left(gene_item["category"]),
                "2px solid #e5e7eb",
            ),
            "backgroundColor": rx.cond(included, "#ffffff", "#fafafa"),
            "transition": "background-color 0.15s ease, border-color 0.15s ease",
            "overflow": "hidden",
        },
        class_name="me-compose-gene-card",
    )


_RPG_PANEL_STYLE: dict = {
    "background": "linear-gradient(180deg, #111827 0%, #0b1020 100%)",
    "border": "1px solid rgba(124, 58, 237, 0.42)",
    "borderRadius": "14px",
    "boxShadow": "0 18px 45px rgba(15, 23, 42, 0.22)",
    "color": "#e5e7eb",
}


def _rpg_panel_title(icon_name: str, title: str, subtitle: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=15, color="#a78bfa"),
            rx.el.span(
                title,
                style={
                    "marginLeft": "8px",
                    "fontSize": "1.08rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#f8fafc",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.cond(
            subtitle != "",
            rx.el.div(
                subtitle,
                style={
                    "fontSize": "0.98rem",
                    "fontWeight": "800",
                    "color": "#c4b5fd",
                    "marginTop": "2px",
                    "lineHeight": "1.35",
                },
            ),
            rx.fragment(),
        ),
        style={"marginBottom": "12px"},
    )


def _rpg_stat_bar(label: str, value: rx.Var | int, color: str, total: int = DEFAULT_BUDGET) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(label, style={"fontSize": "0.9rem", "color": "#cbd5e1", "fontWeight": "800"}),
            rx.el.span(
                value,
                f" / {total} cr",
                style={"fontSize": "0.86rem", "color": "#f8fafc", "fontWeight": "900"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "999px",
                    "background": color,
                    "boxShadow": f"0 0 12px {color}",
                    "width": rx.cond(value > 0, f"calc({value} * 100% / {total})", "0%"),
                    "transition": "width 0.25s ease",
                },
            ),
            style={
                "height": "7px",
                "borderRadius": "999px",
                "backgroundColor": "rgba(148, 163, 184, 0.2)",
                "overflow": "hidden",
            },
        ),
        style={"marginBottom": "9px"},
    )


def _rpg_gene_count_text(count: rx.Var, total_count: int) -> rx.Component:
    return rx.el.span(
        count,
        f" / {total_count} genes",
        style={
            "display": "block",
            "fontSize": "0.78rem",
            "fontWeight": "900",
            "letterSpacing": "0.04em",
            "opacity": "0.86",
            "marginTop": "4px",
            "textTransform": "uppercase",
        },
    )


def _category_anchor_id(category: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in category)
    compact_slug = "-".join(part for part in slug.split("-") if part)
    return f"gene-library-{compact_slug}"


def _category_css_slug(category: str) -> str:
    return _category_anchor_id(category).removeprefix("gene-library-")


def _rpg_category_stat_row(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    tooltip = _category_tooltip(category)
    count = ComposeState.active_display_gene_counts[category]
    spent = ComposeState.active_display_category_prices[category]
    total_count = GAME_CATEGORY_DISPLAY_COUNTS.get(category, 0)
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                fomantic_icon(icon_name, size=14, color=color),
                rx.el.span(
                    category,
                    style={
                        "fontSize": "0.92rem",
                        "fontWeight": "800",
                        "color": "#e5e7eb",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                        "marginLeft": "7px",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "minWidth": "0"},
            ),
            rx.el.span(
                count,
                f"/{total_count}",
                " · ",
                spent,
                " cr",
                style={"fontSize": "0.88rem", "fontWeight": "900", "color": color, "whiteSpace": "nowrap"},
            ),
            style={"display": "flex", "justifyContent": "space-between", "gap": "10px", "marginBottom": "5px"},
        ),
        rx.el.div(
            rx.el.div(
                style={
                    "height": "100%",
                    "borderRadius": "999px",
                    "backgroundColor": color,
                    "boxShadow": f"0 0 10px {color}",
                    "width": rx.cond(count > 0, f"calc({count} * 100% / {total_count})", "0%"),
                    "transition": "width 0.25s ease",
                },
            ),
            style={
                "height": "5px",
                "borderRadius": "999px",
                "backgroundColor": "rgba(148, 163, 184, 0.18)",
                "overflow": "hidden",
            },
        ),
        href=f"#{_category_anchor_id(category)}",
        class_name="me-rpg-category-anchor",
        title=tooltip,
        aria_label=tooltip,
        on_click=ComposeState.open_gene_library_accordion(category),
        style={"display": "block", "marginBottom": "8px", "textDecoration": "none"},
    )


def _rpg_gene_puzzle_icon(gene_item: rx.Var) -> rx.Component:
    return rx.cond(
        gene_item["puzzle_src"] != "",
        rx.el.span(
            rx.el.img(
                src=gene_item["puzzle_src"],
                alt=gene_item["species_common_names"],
                loading="lazy",
                decoding="async",
                style={
                    "display": "block",
                    "maxWidth": "25px",
                    "maxHeight": "25px",
                    "width": "auto",
                    "height": "auto",
                    "objectFit": "contain",
                    "filter": "invert(1) brightness(1.35) drop-shadow(0 0 5px rgba(196, 181, 253, 0.28))",
                },
            ),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "width": "30px",
                "height": "30px",
                "borderRadius": "9px",
                "background": "rgba(248, 250, 252, 0.08)",
                "border": "1px solid rgba(196, 181, 253, 0.24)",
                "flex": "0 0 30px",
            },
        ),
        rx.el.span(
            fomantic_icon("user circle", size=18, color="#c4b5fd"),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "width": "30px",
                "height": "30px",
                "borderRadius": "9px",
                "background": "rgba(248, 250, 252, 0.08)",
                "border": "1px solid rgba(196, 181, 253, 0.18)",
                "flex": "0 0 30px",
            },
        ),
    )


def _rpg_gene_species_label(gene_item: rx.Var) -> rx.Component:
    name_content = rx.el.span(
        rx.el.span(gene_item["species_common_names"], style={"fontWeight": "600"}),
        " ",
        rx.el.span(gene_item["species_scientific_names"], style={"fontStyle": "italic", "opacity": "0.75"}),
        style={"minWidth": "0", "overflow": "hidden", "textOverflow": "ellipsis"},
    )
    return rx.el.div(
        _rpg_gene_puzzle_icon(gene_item),
        rx.cond(
            gene_item["species_page_url"] != "",
            rx.el.a(
                name_content,
                href=gene_item["species_page_url"],
                target="_blank",
                rel="noopener noreferrer",
                style={"textDecoration": "none", "color": "inherit", "_hover": {"textDecoration": "underline"}},
            ),
            name_content,
        ),
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "fontSize": "0.82rem",
            "color": "#94a3b8",
            "marginTop": "6px",
            "minWidth": "0",
        },
    )


def _rpg_selected_gene_chip(gene_item: rx.Var) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            gene_item["gene"],
            style={"fontWeight": "800", "color": "#f8fafc", "fontSize": "0.88rem"},
        ),
        rx.el.span(
            gene_item["category"],
            style={
                "fontSize": "0.74rem",
                "color": _gene_category_accent_color(gene_item["category"]),
                "display": "block",
                "marginTop": "1px",
                "lineHeight": "1.1",
            },
        ),
        rx.el.span(
            "×",
            style={
                "position": "absolute",
                "top": "2px",
                "right": "7px",
                "fontSize": "0.8rem",
                "color": "#94a3b8",
            },
        ),
        on_click=ComposeState.toggle_gene_from_library(gene_item["gene"], gene_item["category"]),
        title="Remove gene",
        style={
            "position": "relative",
            "boxSizing": "border-box",
            "textAlign": "left",
            "padding": "9px 24px 9px 11px",
            "borderRadius": "10px",
            "borderTop": "1px solid rgba(148, 163, 184, 0.32)",
            "borderRight": "1px solid rgba(148, 163, 184, 0.32)",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.32)",
            "borderLeft": _gene_category_border_left(gene_item["category"]),
            "background": "rgba(15, 23, 42, 0.72)",
            "cursor": "pointer",
            "minWidth": "108px",
            "maxWidth": "100%",
        },
    )


def _rpg_schema_hint_panel() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            fomantic_icon("map outline", size=18, color="#22d3ee"),
            rx.el.span(" How it works", style={"marginLeft": "7px"}),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "1.2rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#cffafe",
            },
        ),
        rx.el.div(
            "Process diagram: trait input, parametric geometry, STL, then print. "
            "Open if you want the pictures.",
            style={
                "marginTop": "8px",
                "color": "#cbd5e1",
                "fontSize": "0.82rem",
                "lineHeight": "1.45",
            },
        ),
        rx.el.img(
            src="/images/HOW_IT_WORKS.jpg",
            alt="Materialized Enhancements process flow and instructions",
            loading="lazy",
            decoding="async",
            style={
                "width": "100%",
                "height": "auto",
                "display": "block",
                "marginTop": "10px",
                "borderRadius": "8px",
                "border": "1px solid rgba(148, 163, 184, 0.26)",
                "boxShadow": "0 8px 24px rgba(2, 6, 23, 0.32)",
            },
        ),
        style={
            "marginTop": "0",
            "marginBottom": "0",
            "padding": "14px",
            "borderRadius": "10px",
            "border": "1px solid rgba(34, 211, 238, 0.24)",
            "background": "rgba(8, 47, 73, 0.28)",
            "boxSizing": "border-box",
        },
    )


def _rpg_intro_video_panel() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            fomantic_icon("video", size=18, color="#c4b5fd"),
            rx.el.span(" Project video", style={"marginLeft": "7px"}),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "display": "flex",
                "alignItems": "center",
                "fontSize": "1.2rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#ddd6fe",
            },
        ),
        rx.el.div(
            rx.el.iframe(
                src="https://www.youtube.com/embed/ev726lz5sLo",
                title="Materialized Enhancements project video",
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
                allow_full_screen=True,
                loading="lazy",
                style={
                    "position": "absolute",
                    "top": "0",
                    "left": "0",
                    "width": "100%",
                    "height": "100%",
                    "border": "none",
                    "borderRadius": "8px",
                },
            ),
            style={
                "width": "100%",
                "aspectRatio": "16 / 9",
                "position": "relative",
                "backgroundColor": "#000",
                "borderRadius": "8px",
                "marginTop": "10px",
                "overflow": "hidden",
                "boxShadow": "0 8px 24px rgba(2, 6, 23, 0.32)",
            },
        ),
        style={
            "marginTop": "0",
            "marginBottom": "0",
            "padding": "14px",
            "borderRadius": "10px",
            "border": "1px solid rgba(167, 139, 250, 0.24)",
            "background": "rgba(46, 16, 101, 0.2)",
            "boxSizing": "border-box",
        },
    )


def _onboarding_close_button() -> rx.Component:
    return rx.el.button(
        rx.el.span(
            "×",
            style={
                "fontSize": "1.45rem",
                "lineHeight": "1",
                "fontWeight": "900",
                "color": "#f8fafc",
            },
        ),
        type="button",
        aria_label="Close tip",
        title="Close",
        on_click=ComposeState.advance_onboarding,
        style={
            "position": "relative",
            "zIndex": "1202",
            "flexShrink": "0",
            "width": "38px",
            "height": "38px",
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "borderRadius": "10px",
            "border": "1px solid rgba(148, 163, 184, 0.55)",
            "background": "rgba(30, 41, 59, 0.95)",
            "cursor": "pointer",
            "padding": "0",
        },
    )


def _onboarding_tooltip_card(
    show: rx.Var[bool],
    *,
    step_label: str,
    icon_name: str,
    accent_color: str,
    headline: str,
    detail: str | rx.Var[str],
) -> rx.Component:
    return rx.cond(
        show,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    fomantic_icon(icon_name, size=14, color=accent_color),
                    rx.el.span(
                        step_label,
                        style={
                            "marginLeft": "6px",
                            "fontWeight": "900",
                            "color": accent_color,
                            "fontSize": "0.82rem",
                            "textTransform": "uppercase",
                        },
                    ),
                    style={"display": "flex", "alignItems": "center", "minWidth": "0"},
                ),
                _onboarding_close_button(),
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "flex-start",
                    "gap": "10px",
                    "marginBottom": "8px",
                },
            ),
            rx.el.p(
                headline,
                style={
                    "color": "#f8fafc",
                    "fontSize": "1.12rem",
                    "fontWeight": "900",
                    "lineHeight": "1.4",
                    "margin": "0 0 6px 0",
                },
            ),
            rx.el.p(
                detail,
                style={
                    "color": "#cbd5e1",
                    "fontSize": "0.96rem",
                    "fontWeight": "600",
                    "lineHeight": "1.5",
                    "margin": "0",
                },
            ),
            class_name="me-onboarding-tip-card",
            style={
                "position": "relative",
                "zIndex": "1200",
                "width": "100%",
                "maxWidth": "100%",
                "boxSizing": "border-box",
                "padding": "14px",
                "marginBottom": "12px",
                "borderRadius": "14px",
                "background": "linear-gradient(135deg, #111827 0%, #0b1020 100%)",
                "border": f"2px solid {accent_color}",
                "boxShadow": "0 0 25px rgba(255, 255, 255, 0.70)",
                "pointerEvents": "auto",
            },
        ),
        rx.fragment(),
    )


def _gene_library_onboarding_tooltip() -> rx.Component:
    return _onboarding_tooltip_card(
        ComposeState.show_onboarding_genes,
        step_label="Onboarding: Step 1",
        icon_name="info circle",
        accent_color="#a78bfa",
        headline="Choose your enhancement genes",
        detail=(
            "Click a category icon on the body map (or an accordion below) to highlight and jump to it, "
            "then add genes to your character. "
            "Each gene spends enhancement credits (cr) and shapes your printable crystal — "
            "an abstract form grown from your choices, not a body model yet."
        ),
    )


def _name_onboarding_tooltip() -> rx.Component:
    return _onboarding_tooltip_card(
        ComposeState.show_onboarding_name,
        step_label="Onboarding: Step 2",
        icon_name="user",
        accent_color="#38bdf8",
        headline="Add your name or alias",
        detail=(
            "Please add your name or alias here. It labels your character on the body map, "
            "share card, and personal enhancement report."
        ),
    )


def _materialize_onboarding_tooltip() -> rx.Component:
    return _onboarding_tooltip_card(
        ComposeState.show_onboarding_materialize,
        step_label="Onboarding: Step 3",
        icon_name="atom",
        accent_color="#10b981",
        headline="Materialize when you are ready",
        detail=ComposeState.onboarding_materialize_guidance,
    )


def _rpg_sidebar_intro_stack() -> rx.Component:
    return rx.el.div(
        _rpg_schema_hint_panel(),
        _rpg_intro_video_panel(),
        class_name="me-rpg-sidebar-intro",
    )


def _rpg_selected_gene_loadout() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _rpg_panel_title("dna", "Active genes", "Selected genes are the actual input to materialization."),
            style={
                "marginBottom": "2px",
            },
        ),
        rx.cond(
            ComposeState.budget_spent > 0,
            rx.el.div(
                rx.foreach(ComposeState.included_gene_chips, _rpg_selected_gene_chip),
                rx.el.button(
                    fomantic_icon("times", size=12),
                    rx.el.span(" Deselect all", style={"marginLeft": "5px"}),
                    on_click=ComposeState.deselect_all_genes,
                    class_name="ui button",
                    style={
                        "padding": "7px 10px",
                        "fontSize": "0.76rem",
                        "fontWeight": "800",
                        "whiteSpace": "nowrap",
                    },
                ),
                style={
                    "display": "flex",
                    "flexWrap": "wrap",
                    "gap": "8px",
                    "alignItems": "stretch",
                },
            ),
            rx.el.div(
                rx.el.div(
                    "Add genes from the Gene library below.",
                    style={
                        "padding": "12px",
                        "borderRadius": "10px",
                        "border": "1px dashed rgba(148, 163, 184, 0.35)",
                        "color": "#94a3b8",
                        "fontSize": "0.84rem",
                        "lineHeight": "1.45",
                    },
                ),
                style={"display": "flex", "flexDirection": "column", "gap": "10px"},
            ),
        ),
        _materialize_hint_bubble("genes"),
        style={**_RPG_PANEL_STYLE, "padding": "14px", "marginBottom": "12px", "position": "relative"},
    )


def _rpg_materialization_leg_cta() -> rx.Component:
    return rx.el.div(
        _materialize_onboarding_tooltip(),
        rx.el.button(
            rx.cond(
                ComposeState.generating,
                fomantic_icon("sync", size=20, style={"animation": "me-spin 1s linear infinite"}),
                fomantic_icon("atom", size=20),
            ),
            rx.el.span(
                rx.cond(ComposeState.generating, " Generating...", " Materialize"),
                style={"marginLeft": "8px"},
            ),
            on_click=ComposeState.materialize,
            disabled=rx.cond(
                ComposeState.generating,
                True,
                rx.cond(ComposeState.can_materialize, False, True),
            ),
            class_name=rx.cond(
                ComposeState.generating,
                "me-rpg-materialize-leg-button is-disabled",
                rx.cond(
                    ComposeState.can_materialize,
                    "me-rpg-materialize-leg-button is-active-pulse",
                    "me-rpg-materialize-leg-button is-disabled",
                ),
            ),
            title=rx.cond(
                ComposeState.can_materialize,
                "Grow your printable crystal and report.",
                ComposeState.materialize_requirements_notice,
            ),
        ),
        class_name=rx.cond(
            ComposeState.show_onboarding_materialize,
            "me-rpg-materialize-leg-cta me-onboarding-materialize-lift",
            "me-rpg-materialize-leg-cta",
        ),
        on_mouse_enter=ComposeState.show_materialize_hint,
        on_mouse_leave=ComposeState.hide_materialize_hint,
    )


def _rpg_marker_gene_chip(gene_item: rx.Var, category: str, color: str) -> rx.Component:
    return rx.el.span(
        gene_item["label"],
        class_name="me-rpg-marker-gene-chip",
        title="Right-click to remove",
        on_context_menu=[
            ComposeState.remove_gene_marker_shortcut(gene_item["gene"], category),
            rx.prevent_default,
        ],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "position": "relative",
            "zIndex": "2",
            "width": "72px",
            "minHeight": "24px",
            "padding": "2px 6px",
            "borderRadius": "6px",
            "border": f"1px solid {color}99",
            "background": "rgba(15, 23, 42, 0.96)",
            "boxShadow": f"0 0 12px {color}55",
            "color": "#f8fafc",
            "fontSize": "0.72rem",
            "fontWeight": "950",
            "lineHeight": "1.15",
            "letterSpacing": "0.02em",
            "textShadow": "0 1px 8px rgba(0, 0, 0, 0.85)",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "pointerEvents": "auto",
            "cursor": "context-menu",
        },
    )


def _rpg_marker_gene_orbit_item(gene_item: rx.Var, category: str, color: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name="me-rpg-marker-gene-line",
            style={
                "position": "absolute",
                "right": "50%",
                "top": "50%",
                "height": "2px",
                "borderRadius": "999px",
                "background": f"linear-gradient(90deg, {color}cc, {color}11)",
                "boxShadow": f"0 0 8px {color}88",
                "pointerEvents": "none",
                "transformOrigin": "right center",
                "zIndex": "0",
            },
        ),
        _rpg_marker_gene_chip(gene_item, category, color),
        class_name="me-rpg-marker-gene-orbit-item",
        style={
            "position": "absolute",
            "left": "50%",
            "top": "50%",
            "pointerEvents": "none",
            "zIndex": "1",
        },
    )


_ICON_VISUAL_NUDGE: dict[str, tuple[int, int]] = {
    "paint brush": (1, 0),
    "eye": (-1, 1),
    "heartbeat": (2, 1),
    "shield": (2, 0),
    "globe": (2, 0),
    "sync": (1, 0),
    "camera": (3, 0),
}


def _rpg_silhouette_marker(
    category: str,
    top: str,
    left: str,
) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    tooltip = _category_tooltip(category)
    count = ComposeState.active_display_gene_counts[category]
    is_selected = ComposeState.selected_categories.contains(category)
    is_affordable = ComposeState.affordable_categories.contains(category)
    is_enabled = is_selected | is_affordable
    visual_active = is_selected | (count > 0)
    return rx.el.a(
        rx.el.div(
            rx.cond(
                count > 0,
                rx.el.div(
                    rx.foreach(
                        ComposeState.active_compact_gene_names_by_category[category],
                        lambda gene_item: _rpg_marker_gene_orbit_item(gene_item, category, color),
                    ),
                    class_name="me-rpg-marker-gene-orbit",
                    style={
                        "position": "absolute",
                        "left": "50%",
                        "top": "50%",
                        "width": "188px",
                        "height": "156px",
                        "transform": "translate(-50%, -50%)",
                        "pointerEvents": "none",
                        "zIndex": "1",
                    },
                ),
                rx.fragment(),
            ),
            rx.el.div(
                rx.el.div(
                    fomantic_icon(
                        icon_name,
                        size=22,
                        color=color,
                    ),
                    style={
                        "position": "absolute",
                        "top": "50%",
                        "left": "50%",
                        "transform": f"translate(calc(-50% + {_ICON_VISUAL_NUDGE.get(icon_name, (0, 0))[0]}px), calc(-50% + {_ICON_VISUAL_NUDGE.get(icon_name, (0, 0))[1]}px)) scale(0.70)",
                        "transformOrigin": "center",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "lineHeight": "1",
                    },
                ),
                rx.cond(
                    count > 0,
                    rx.el.span(
                        count,
                        class_name="me-rpg-marker-count-badge",
                        style={
                            "position": "absolute",
                            "right": "-6px",
                            "top": "-6px",
                            "minWidth": "24px",
                            "height": "24px",
                            "padding": "0 5px",
                            "display": "inline-flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "borderRadius": "999px",
                            "border": "2px solid rgba(15, 23, 42, 0.96)",
                            "background": color,
                            "color": "#ffffff",
                            "fontSize": "0.74rem",
                            "fontWeight": "950",
                            "lineHeight": "1",
                            "boxShadow": f"0 0 16px {color}aa",
                        },
                    ),
                    rx.fragment(),
                ),
                class_name="me-rpg-marker-icon-node",
                style={
                    "position": "relative",
                    "width": "65px",
                    "height": "65px",
                    "borderRadius": "999px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "background": rx.cond(visual_active, f"linear-gradient(135deg, {color}44, #111827)", f"linear-gradient(135deg, {color}22, rgba(15, 23, 42, 0.9))"),
                    "border": rx.cond(visual_active, f"2px solid {color}", f"1px solid {color}88"),
                    "boxShadow": rx.cond(visual_active, f"0 0 38px {color}", f"0 0 16px {color}33"),
                    "opacity": rx.cond(is_enabled, rx.cond(visual_active, "1", "0.7"), "0.42"),
                    "zIndex": "2",
                },
            ),
            class_name="me-rpg-marker-orbit-shell",
            style={
                "position": "relative",
                "width": "188px",
                "height": "156px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        ),
        rx.el.div(
            rx.el.span(
                category,
                style={
                    "display": "block",
                    "fontSize": "0.98rem",
                    "fontWeight": "950",
                    "letterSpacing": "0.02em",
                    "textTransform": "none",
                    "whiteSpace": "nowrap",
                },
            ),
            class_name="me-rpg-marker-label",
            style={
                "position": "absolute",
                "left": "50%",
                "top": "calc(50% + 46px)",
                "transform": "translateX(-50%)",
                "marginTop": "0",
                "padding": "5px 10px",
                "boxSizing": "border-box",
                "width": "max-content",
                "borderRadius": "6px",
                "background": "rgba(15, 23, 42, 0.72)",
                "border": f"1px solid {color}55",
                "fontSize": "0.98rem",
                "fontWeight": "900",
                "color": rx.cond(visual_active, "#e0f2fe", "#94a3b8"),
                "textShadow": "0 1px 8px rgba(0, 0, 0, 0.85)",
                "lineHeight": "1.2",
                "maxWidth": "280px",
                "textAlign": "center",
                "boxShadow": "0 8px 20px rgba(2, 6, 23, 0.26)",
            },
        ),
        on_click=ComposeState.select_category(category),
        href=f"#{_category_anchor_id(category)}",
        role="button",
        aria_disabled=rx.cond(is_enabled, "false", "true"),
        title=tooltip,
        aria_label=tooltip,
        class_name=f"me-rpg-body-marker me-rpg-body-marker--{_category_css_slug(category)}",
        style={
            "position": "absolute",
            "top": top,
            "left": left,
            "transform": "translate(-50%, -50%)",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "background": "transparent",
            "border": "none",
            "padding": "0",
            "cursor": "pointer",
            "zIndex": "2",
            "textDecoration": "none",
            "width": "188px",
            "height": "156px",
        },
    )


def _debounced_personal_tag_input(
    *,
    input_id: str,
    style: dict,
) -> rx.Component:
    """Client-buffered name field — syncs only after idle / blur / Enter.

    Do not attach server ``on_key_down`` handlers here: every key would round-trip
    over WebSocket and reintroduce dropped characters.
    """
    return rx.debounce_input(
        rx.el.input(
            id=input_id,
            # nickname — not a legal/cardholder name. Without this, Chrome
            # classifies the field as NAME and offers wallet cardholder names.
            name="character-alias",
            auto_complete="nickname",
            placeholder="Enhanced <Name>",
            value=ComposeState.personal_tag,
            on_change=ComposeState.set_personal_tag,
            style=style,
        ),
        debounce_timeout=1500,
        force_notify_on_blur=True,
        force_notify_by_enter=True,
    )


def _personal_tag_enter_onboarding_script() -> rx.Component:
    """Enter in the name field advances onboarding without per-keystroke server events."""
    return rx.script(
        """
        (() => {
            if (window.__meNameEnterOnboardingInstalled) return;
            window.__meNameEnterOnboardingInstalled = true;
            document.addEventListener('keydown', (event) => {
                const target = event.target;
                if (!target || target.id !== 'compose-personal-tag') return;
                if (event.key !== 'Enter') return;
                event.preventDefault();
                // Let react-debounce-input flush onChange via force_notify_by_enter first.
                setTimeout(() => {
                    const btn = document.getElementById('me-advance-name-onboarding');
                    if (btn) btn.click();
                }, 0);
            }, true);
        })();
        """
    )


def _rpg_body_map_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    _name_onboarding_tooltip(),
                    rx.el.div(
                        _debounced_personal_tag_input(
                            input_id="compose-personal-tag",
                            style={
                                "flex": "1",
                                "minWidth": "0",
                                "padding": "10px 14px",
                                "borderRadius": "12px",
                                "border": rx.cond(
                                    ComposeState.has_personal_tag,
                                    "1px solid rgba(167, 139, 250, 0.45)",
                                    "2px solid rgba(248, 113, 113, 0.95)",
                                ),
                                "fontSize": "0.98rem",
                                "fontWeight": "800",
                                "outline": "none",
                                "backgroundColor": "rgba(15, 23, 42, 0.88)",
                                "color": "#f8fafc",
                                "boxSizing": "border-box",
                                "boxShadow": rx.cond(
                                    ComposeState.has_personal_tag,
                                    "0 0 24px rgba(124, 58, 237, 0.45), 0 0 52px rgba(56, 189, 248, 0.20)",
                                    "0 0 0 3px rgba(248, 113, 113, 0.16), 0 0 24px rgba(248, 113, 113, 0.35)",
                                ),
                            },
                        ),
                        rx.el.button(
                            id="me-advance-name-onboarding",
                            type="button",
                            on_click=ComposeState.advance_name_onboarding_from_enter,
                            style={"display": "none"},
                            aria_hidden="true",
                            tab_index=-1,
                        ),
                        _personal_tag_enter_onboarding_script(),
                        rx.upload(
                            rx.cond(
                                ComposeState.has_report_portrait,
                                rx.el.img(
                                    src=ComposeState.report_portrait_data_url,
                                    alt="Portrait",
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "objectFit": "cover",
                                        "borderRadius": "999px",
                                    },
                                ),
                                rx.el.div(
                                    fomantic_icon("camera", size=18, color="#a78bfa"),
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                        "borderRadius": "999px",
                                        "transform": f"translate({_ICON_VISUAL_NUDGE.get('camera', (0, 0))[0]}px, {_ICON_VISUAL_NUDGE.get('camera', (0, 0))[1]}px)",
                                    },
                                ),
                            ),
                            id=_HERO_PORTRAIT_UPLOAD_ID,
                            on_drop=ComposeState.upload_report_portrait(
                                rx.upload_files(upload_id=_HERO_PORTRAIT_UPLOAD_ID)
                            ),
                            border="none",
                            padding="0",
                            style={
                                "width": "52px",
                                "height": "52px",
                                "flexShrink": "0",
                                "borderRadius": "999px",
                                "border": "2px solid rgba(167, 139, 250, 0.52)",
                                "backgroundColor": "rgba(15, 23, 42, 0.72)",
                                "cursor": "pointer",
                                "overflow": "hidden",
                                "boxShadow": "0 0 16px rgba(124, 58, 237, 0.24)",
                            },
                        ),
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "10px",
                        },
                    ),
                    _materialize_hint_bubble("name"),
                    style=rx.cond(
                        ComposeState.show_onboarding_name,
                        {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0px",
                            "marginBottom": "7px",
                            "position": "relative",
                            "zIndex": "1010",
                            "padding": "10px",
                            "borderRadius": "14px",
                            "boxShadow": "0 0 25px rgba(255, 255, 255, 0.70)",
                            "background": "rgba(15, 23, 42, 0.92)",
                        },
                        {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "0px",
                            "marginBottom": "7px",
                            "position": "relative",
                        },
                    ),
                ),
                class_name="me-rpg-body-map-title",
            ),
            style={
                "marginBottom": "2px",
            },
        ),
        rx.el.div(
            _rpg_silhouette_marker("Expression", "12%", "22%"),
            _rpg_silhouette_marker("Perception", "12%", "78%"),
            _rpg_silhouette_marker("Longevity & Genome", "48%", "22%"),
            _rpg_silhouette_marker("Stress Resistance", "48%", "78%"),
            _rpg_silhouette_marker("Environmental Adaptation", "76%", "22%"),
            _rpg_silhouette_marker("Regeneration", "76%", "78%"),
            rx.el.img(
                src="/images/body_only.webp",
                alt="Transparent human body centered in the enhancement map",
                class_name="me-rpg-body-image",
            ),
            _rpg_materialization_leg_cta(),
            class_name="me-rpg-body-stage",
        ),
        class_name="me-rpg-body-map-panel",
    )


def _mobile_overlay_body_marker(category: str, top: str, left: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    count = ComposeState.active_display_gene_counts[category]
    return rx.el.div(
        rx.cond(
            count > 0,
            rx.el.span(
                count,
                style={
                    "position": "absolute",
                    "right": "-6px",
                    "top": "-6px",
                    "minWidth": "17px",
                    "height": "17px",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "borderRadius": "999px",
                    "border": "1px solid rgba(15, 23, 42, 0.96)",
                    "background": color,
                    "color": "#ffffff",
                    "fontSize": "0.58rem",
                    "fontWeight": "950",
                    "lineHeight": "1",
                },
            ),
            rx.fragment(),
        ),
        class_name=f"me-mobile-overlay-marker me-mobile-overlay-marker--{_category_css_slug(category)}",
        style={
            "position": "absolute",
            "top": top,
            "left": left,
            "width": "26px",
            "height": "26px",
            "borderRadius": "999px",
            "transform": "translate(-50%, -50%)",
            "background": rx.cond(count > 0, color, f"{color}44"),
            "border": f"1px solid {color}",
            "boxShadow": rx.cond(count > 0, f"0 0 16px {color}", f"0 0 8px {color}66"),
            "opacity": rx.cond(count > 0, "1", "0.55"),
        },
    )


def _mobile_body_change_overlay() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                _mobile_overlay_body_marker("Expression", "17%", "35%"),
                _mobile_overlay_body_marker("Perception", "17%", "65%"),
                _mobile_overlay_body_marker("Longevity & Genome", "48%", "35%"),
                _mobile_overlay_body_marker("Stress Resistance", "48%", "65%"),
                _mobile_overlay_body_marker("Environmental Adaptation", "77%", "35%"),
                _mobile_overlay_body_marker("Regeneration", "77%", "65%"),
                rx.el.img(
                    src="/images/body_only.webp",
                    alt="Mini enhanced body preview",
                    style={
                        "height": "120px",
                        "width": "82px",
                        "objectFit": "contain",
                        "display": "block",
                        "filter": "drop-shadow(0 0 12px rgba(56, 189, 248, 0.44))",
                    },
                ),
                class_name="me-mobile-body-change-mini-stage",
            ),
            rx.el.div(
                rx.el.div(
                    "Character updated",
                    style={
                        "fontSize": "0.72rem",
                        "fontWeight": "950",
                        "letterSpacing": "0.08em",
                        "textTransform": "uppercase",
                        "color": "#a78bfa",
                    },
                ),
                rx.el.div(
                    ComposeState.mobile_change_overlay_gene,
                    style={
                        "marginTop": "2px",
                        "fontSize": "0.96rem",
                        "fontWeight": "950",
                        "lineHeight": "1.18",
                        "color": "#f8fafc",
                    },
                ),
                rx.el.div(
                    ComposeState.mobile_change_overlay_category,
                    style={
                        "marginTop": "3px",
                        "fontSize": "0.78rem",
                        "fontWeight": "800",
                        "lineHeight": "1.2",
                        "color": "#cbd5e1",
                    },
                ),
                style={"minWidth": "0", "flex": "1"},
            ),
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
            },
        ),
        id="me-mobile-body-change-overlay",
        class_name="me-mobile-body-change-overlay",
        aria_live="polite",
        style={
            "position": "fixed",
            "right": "14px",
            "bottom": "14px",
            "zIndex": "1400",
            "width": "min(360px, calc(100vw - 28px))",
            "padding": "10px 12px",
            "borderRadius": "18px",
            "border": "1px solid rgba(167, 139, 250, 0.55)",
            "background": "rgba(15, 23, 42, 0.94)",
            "boxShadow": "0 20px 48px rgba(2, 6, 23, 0.58), 0 0 28px rgba(124, 58, 237, 0.32)",
            "backdropFilter": "blur(14px)",
            "WebkitBackdropFilter": "blur(14px)",
            "pointerEvents": "none",
        },
    )


def _rpg_gene_side_text(title: str, segments: rx.Var) -> rx.Component:
    return rx.cond(
        segments.length() > 0,
        rx.el.div(
            rx.el.div(
                title,
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#94a3b8",
                    "marginBottom": "4px",
                },
            ),
            rx.el.div(
                rx.foreach(segments, _gene_prose_segment),
                style={
                    "fontSize": "0.86rem",
                    "lineHeight": "1.45",
                    "color": "#cbd5e1",
                    "whiteSpace": "pre-wrap",
                },
            ),
            style={
                "padding": "10px 11px",
                "borderRadius": "7px",
                "backgroundColor": "rgba(15, 23, 42, 0.42)",
                "border": "1px solid rgba(148, 163, 184, 0.18)",
            },
        ),
        rx.fragment(),
    )


def _rpg_gene_side_references(segments: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Key references",
            style={
                "fontSize": "0.95rem",
                "fontWeight": "900",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color": "#94a3b8",
                "marginBottom": "4px",
            },
        ),
        rx.el.p(
            rx.foreach(segments, _gene_key_reference_segment),
            style={
                "fontSize": "0.82rem",
                "lineHeight": "1.42",
                "margin": "0",
                "whiteSpace": "pre-wrap",
            },
        ),
        style={
            "padding": "10px 11px",
            "borderRadius": "7px",
            "backgroundColor": "rgba(15, 23, 42, 0.42)",
            "border": "1px solid rgba(148, 163, 184, 0.18)",
        },
    )


_STRUCTURE_LINK_STYLE: dict = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "4px",
    "padding": "6px 12px",
    "borderRadius": "6px",
    "border": "1px solid rgba(167, 139, 250, 0.38)",
    "background": "rgba(124, 58, 237, 0.14)",
    "color": "#c4b5fd",
    "fontSize": "0.82rem",
    "fontWeight": "700",
    "textDecoration": "none",
    "cursor": "pointer",
    "_hover": {
        "background": "rgba(124, 58, 237, 0.28)",
        "color": "#e9d5ff",
        "borderColor": "rgba(167, 139, 250, 0.6)",
    },
}


def _gene_id_chip(
    label: rx.Var | str,
    value: rx.Var,
    href: rx.Var,
    dark: bool,
) -> rx.Component:
    """Visible accession chip; links out when a database URL exists."""
    text_color = "#e2e8f0" if dark else "#374151"
    muted = "#94a3b8" if dark else "#6b7280"
    chip = rx.el.span(
        rx.el.span(label, style={"color": muted, "fontWeight": "600", "marginRight": "5px"}),
        rx.el.span(value, style={"fontWeight": "800", "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace"}),
        style={"fontSize": "0.78rem", "color": text_color},
    )
    return rx.cond(
        value != "",
        rx.cond(
            href != "",
            rx.el.a(
                chip,
                href=href,
                target="_blank",
                rel="noopener noreferrer",
                title="Open accession",
                style={"textDecoration": "none", "borderBottom": "1px dotted rgba(167, 139, 250, 0.55)"},
            ),
            chip,
        ),
        rx.fragment(),
    )


def _gene_protein_id_row(gene_item: rx.Var, dark: bool) -> rx.Component:
    """UniProt / NCBI / PDB accessions plus a reference-protein fallback."""
    return rx.el.div(
        _gene_id_chip(gene_item["protein_id_label"], gene_item["protein_id"], gene_item["gene_url"], dark),
        _gene_id_chip("PDB", gene_item["pdb_id"], gene_item["pdb_url"], dark),
        rx.cond(
            (gene_item["protein_id"] == "") & (gene_item["reference_protein"] != ""),
            rx.el.span(
                "Ref ",
                gene_item["reference_protein"],
                style={
                    "fontSize": "0.78rem",
                    "color": "#94a3b8" if dark else "#6b7280",
                    "fontWeight": "600",
                },
            ),
            rx.fragment(),
        ),
        style={"display": "flex", "alignItems": "center", "gap": "10px", "flexWrap": "wrap"},
    )


def _gene_stl_block(gene_item: rx.Var, dark: bool) -> rx.Component:
    """Printable protein STL download and print metadata."""
    text = "#cbd5e1" if dark else "#374151"
    muted = "#94a3b8" if dark else "#6b7280"
    return rx.cond(
        gene_item["stl_file"] != "",
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Printable protein",
                    style={
                        "fontSize": "0.82rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.06em",
                        "textTransform": "uppercase",
                        "color": muted,
                    },
                ),
                rx.el.button(
                    fomantic_icon("download", size=11, color="#c4b5fd" if dark else "#6d28d9"),
                    rx.el.span(" STL", style={"fontSize": "0.74rem", "fontWeight": "700"}),
                    on_click=ComposeState.download_protein_stl(gene_item["gene"]),
                    type="button",
                    title="Download printable protein STL",
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "gap": "3px",
                        "padding": "4px 9px",
                        "borderRadius": "6px",
                        "border": "1px solid rgba(124, 58, 237, 0.35)",
                        "background": "rgba(124, 58, 237, 0.16)",
                        "color": "#c4b5fd" if dark else "#6d28d9",
                        "cursor": "pointer",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "8px"},
            ),
            rx.el.div(
                rx.cond(
                    gene_item["stl_source_label"] != "",
                    rx.el.span(gene_item["stl_source_label"]),
                    rx.fragment(),
                ),
                rx.cond(
                    gene_item["stl_difficulty"] != "",
                    rx.el.span(" · ", gene_item["stl_difficulty"], " print"),
                    rx.fragment(),
                ),
                rx.cond(
                    gene_item["stl_dimensions_mm"] != "",
                    rx.el.span(" · ", gene_item["stl_dimensions_mm"], " mm"),
                    rx.fragment(),
                ),
                rx.cond(
                    gene_item["stl_triangles"] != "",
                    rx.el.span(" · ", gene_item["stl_triangles"], " tris"),
                    rx.fragment(),
                ),
                style={"fontSize": "0.78rem", "color": text, "marginTop": "4px"},
            ),
            style={
                "padding": "10px 11px",
                "borderRadius": "7px",
                "background": "rgba(15, 23, 42, 0.42)" if dark else "#ffffff",
                "border": "1px solid rgba(167, 139, 250, 0.28)" if dark else "1px solid #d4c5f9",
            },
        ),
        rx.fragment(),
    )


def _gene_structure_viewer(gene_item: rx.Var) -> rx.Component:
    """Interactive 3D protein structure viewer or fallback external links.

    Mounted only under an open Details panel; 3Dmol is fetched when the viewer
    node appears, not on initial page load.
    """
    has_local = gene_item["structure_pdb"] != ""
    has_pdb_url = gene_item["pdb_url"] != ""
    has_af_url = gene_item["alphafold_url"] != ""

    link_row = rx.el.div(
        rx.cond(
            has_pdb_url,
            rx.el.a(
                fomantic_icon("database", size=13, color="#a78bfa"),
                " RCSB PDB ",
                gene_item["pdb_id"],
                href=gene_item["pdb_url"],
                target="_blank",
                rel="noopener noreferrer",
                title="View on RCSB PDB",
                style=_STRUCTURE_LINK_STYLE,
            ),
            rx.fragment(),
        ),
        rx.cond(
            has_af_url,
            rx.el.a(
                fomantic_icon("cube", size=13, color="#a78bfa"),
                " AlphaFold",
                href=gene_item["alphafold_url"],
                target="_blank",
                rel="noopener noreferrer",
                title="View on AlphaFold DB",
                style=_STRUCTURE_LINK_STYLE,
            ),
            rx.fragment(),
        ),
        style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
    )

    viewer_with_links = rx.el.div(
        rx.el.div(
            fomantic_icon("cube", size=14, color="#a78bfa"),
            rx.el.span(
                " Protein 3D Structure",
                style={"marginLeft": "6px", "fontWeight": "700", "fontSize": "0.88rem"},
            ),
            style={"display": "flex", "alignItems": "center", "color": "#c4b5fd", "marginBottom": "8px"},
        ),
        rx.el.div(
            class_name="me-pdb-viewer",
            custom_attrs={"data-pdb-src": "/structures/" + gene_item["structure_pdb"]},
            style={
                "width": "100%",
                "height": "320px",
                "borderRadius": "8px",
                "border": "1px solid rgba(167, 139, 250, 0.28)",
                "background": "#0f172a",
                "position": "relative",
                "overflow": "hidden",
            },
        ),
        rx.el.div(
            link_row,
            style={"marginTop": "6px"},
        ),
        style={
            "padding": "10px",
            "borderRadius": "10px",
            "border": "1px solid rgba(167, 139, 250, 0.22)",
            "background": "rgba(15, 23, 42, 0.6)",
        },
    )

    return rx.cond(
        has_local,
        viewer_with_links,
        rx.cond(
            has_pdb_url | has_af_url,
            link_row,
            rx.fragment(),
        ),
    )


def _gene_fold_text(title: str, segments: rx.Var, dark: bool) -> rx.Component:
    return rx.cond(
        segments.length() > 0,
        rx.el.div(
            rx.el.div(
                title,
                style={
                    "fontSize": "0.82rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.07em",
                    "textTransform": "uppercase",
                    "color": "#94a3b8" if dark else "#6b7280",
                    "marginBottom": "4px",
                },
            ),
            rx.el.div(
                rx.foreach(segments, _gene_prose_segment),
                style={
                    "fontSize": "0.9rem",
                    "lineHeight": "1.55",
                    "color": "#cbd5e1" if dark else "#374151",
                    "whiteSpace": "pre-wrap",
                },
            ),
            style={
                "padding": "10px 11px",
                "borderRadius": "7px",
                "background": "rgba(15, 23, 42, 0.42)" if dark else "#ffffff",
                "border": (
                    "1px solid rgba(148, 163, 184, 0.18)"
                    if dark
                    else "1px solid #e5e7eb"
                ),
            },
        ),
        rx.fragment(),
    )


def _gene_fold_property(label: str, value: rx.Var, dark: bool) -> rx.Component:
    return rx.cond(
        value != "",
        rx.el.div(
            rx.el.span(
                label,
                style={
                    "fontSize": "0.84rem",
                    "color": "#94a3b8" if dark else "#6b7280",
                },
            ),
            rx.el.span(
                value,
                style={
                    "fontSize": "0.84rem",
                    "fontWeight": "700",
                    "color": "#e2e8f0" if dark else "#374151",
                    "textAlign": "right",
                },
            ),
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "gap": "12px",
                "padding": "5px 0",
                "borderBottom": (
                    "1px solid rgba(148, 163, 184, 0.12)"
                    if dark
                    else "1px solid #f3f4f6"
                ),
            },
        ),
        rx.fragment(),
    )


def _gene_fold_button(
    label: str,
    icon_name: str,
    dark: bool,
) -> rx.Component:
    idle_background = "rgba(30, 41, 59, 0.56)" if dark else "#ffffff"
    return rx.el.summary(
        rx.el.span(
            fomantic_icon(
                icon_name,
                size=15,
                color="#c4b5fd" if dark else "#6d28d9",
            ),
            rx.el.span(label),
            style={"display": "inline-flex", "alignItems": "center", "gap": "9px"},
        ),
        rx.el.span(
            rx.el.span(
                "Show",
                class_name="me-gene-fold-show",
                style={
                    "fontSize": "0.76rem",
                    "fontWeight": "700",
                    "color": "#c4b5fd" if dark else "#7c3aed",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                },
            ),
            rx.el.span(
                "Hide",
                class_name="me-gene-fold-hide",
                style={
                    "display": "none",
                    "fontSize": "0.76rem",
                    "fontWeight": "700",
                    "color": "#c4b5fd" if dark else "#7c3aed",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.06em",
                },
            ),
            rx.el.span(
                fomantic_icon(
                    "chevron down",
                    size=12,
                    color="#c4b5fd" if dark else "#6d28d9",
                ),
                class_name="me-gene-fold-chevron",
                style={"display": "inline-flex", "transition": "transform 0.16s ease"},
            ),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "flex-end",
                "gap": "8px",
                "minWidth": "72px",
                "flexShrink": "0",
            },
        ),
        title="Expand or collapse " + label,
        style={
            "width": "100%",
            "boxSizing": "border-box",
            "minWidth": "0",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "gap": "12px",
            "padding": "12px 14px",
            "border": "0",
            "listStyle": "none",
            "background": idle_background,
            "color": "#f5f3ff" if dark else "#6d28d9",
            "fontSize": "0.96rem",
            "fontWeight": "900",
            "cursor": "pointer",
            "textAlign": "left",
        },
    )


def _gene_fold_item(
    section: str,
    label: str,
    icon_name: str,
    content: rx.Component,
    dark: bool,
) -> rx.Component:
    return rx.el.details(
        _gene_fold_button(
            label,
            icon_name,
            dark,
        ),
        content,
        class_name=f"me-gene-information-fold me-gene-information-fold-{section}",
        style={
            "width": "100%",
            "boxSizing": "border-box",
            "minWidth": "0",
            "borderRadius": "9px",
            "overflow": "hidden",
            "border": (
                "1px solid rgba(167, 139, 250, 0.42)"
                if dark
                else "1px solid #d4c5f9"
            ),
            "boxShadow": "none",
        },
    )


def _gene_ai_provider_button(
    gene_id: rx.Var,
    *,
    label: str,
    provider: str,
    icon_src: str,
) -> rx.Component:
    return rx.el.button(
        rx.el.img(
            src=icon_src,
            alt="",
            width="14",
            height="14",
            style={"width": "14px", "height": "14px", "display": "block"},
        ),
        type="button",
        on_click=ComposeState.open_gene_ai(gene_id, provider),
        aria_label=f"Ask {label} about this gene",
        title=f"Ask {label} about this gene",
        style={
            "width": "21px",
            "height": "21px",
            "padding": "0",
            "borderRadius": "999px",
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "background": "#f8fafc",
            "border": "1px solid rgba(148, 163, 184, 0.38)",
            "cursor": "pointer",
            "opacity": "0.9",
        },
    )


def _gene_ai_controls(gene_item: rx.Var, dark: bool) -> rx.Component:
    gene_id = gene_item["gene_id"]
    return rx.el.div(
        rx.el.span(
            "Ask AI about " + gene_item["gene"],
            style={
                "fontSize": "0.65rem",
                "fontWeight": "700",
                "color": "#94a3b8" if dark else "#6b7280",
                "lineHeight": "1.2",
            },
        ),
        rx.el.div(
            _gene_ai_provider_button(
                gene_id,
                label="ChatGPT",
                provider="chatgpt",
                icon_src="/images/icons/openai.svg",
            ),
            _gene_ai_provider_button(
                gene_id,
                label="Claude",
                provider="claude",
                icon_src="/images/icons/claude.svg",
            ),
            _gene_ai_provider_button(
                gene_id,
                label="Grok",
                provider="grok",
                icon_src="/images/icons/grok.svg",
            ),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "gap": "6px",
                "flexShrink": "0",
            },
        ),
        class_name="me-gene-ai-controls",
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "flex-start",
            "gap": "10px",
            "flexWrap": "wrap",
        },
    )


def _gene_information_folds(gene_item: rx.Var, dark: bool) -> rx.Component:
    has_organizations = gene_item["org_entries"].length() > 0
    has_structure = (
        (gene_item["structure_pdb"] != "")
        | (gene_item["pdb_url"] != "")
        | (gene_item["alphafold_url"] != "")
        | (gene_item["protein_id"] != "")
        | (gene_item["pdb_id"] != "")
        | (gene_item["stl_file"] != "")
        | (gene_item["protein_mass_kda"] != "")
        | (gene_item["reference_protein"] != "")
    )
    section_style = {
        "display": "flex",
        "flexDirection": "column",
        "gap": "8px",
        "padding": "12px",
        "background": "rgba(15, 23, 42, 0.3)" if dark else "#fafafa",
        "borderTop": (
            "1px solid rgba(167, 139, 250, 0.3)"
            if dark
            else "1px solid #d4c5f9"
        ),
    }

    mechanism_content = rx.el.div(
        _gene_fold_text(
            "Full description",
            gene_item["narrative_segments"],
            dark,
        ),
        _gene_fold_text(
            "Mechanism",
            gene_item["mechanism_segments"],
            dark,
        ),
        _gene_fold_text(
            "Translational gaps",
            gene_item["translational_gaps_segments"],
            dark,
        ),
        _gene_fold_text("Notes", gene_item["notes_segments"], dark),
        _gene_fold_property("Exon count", gene_item["exon_count"], dark),
        _gene_fold_property(
            "Genes in system",
            gene_item["genes_in_system"],
            dark,
        ),
        style=section_style,
    )
    evidence_content = rx.el.div(
        _gene_confidence_section(
            gene_item["confidence_primary"],
            gene_item["confidence_details"],
            show_details=True,
        ),
        _gene_fold_text(
            "Achievements (effect sizes)",
            gene_item["achievements_segments"],
            dark,
        ),
        _gene_tested_on_row(gene_item["testing_entries"]),
        _gene_testing_records(gene_item["testing_entries"]),
        rx.cond(
            gene_item["key_reference_segments"].length() > 0,
            (
                _rpg_gene_side_references(gene_item["key_reference_segments"])
                if dark
                else _gene_key_references_linked(gene_item["key_reference_segments"])
            ),
            rx.fragment(),
        ),
        _gene_fold_property(
            "Recipient organism count",
            gene_item["recipient_organism_count"],
            dark,
        ),
        _gene_fold_property(
            "Key publication year",
            gene_item["key_publication_year"],
            dark,
        ),
        style=section_style,
    )
    organizations_content = rx.el.div(
        _gene_organizations_section(gene_item["org_entries"]),
        style=section_style,
    )
    structure_content = rx.el.div(
        _gene_protein_id_row(gene_item, dark),
        _gene_structure_viewer(gene_item),
        _gene_stl_block(gene_item, dark),
        _gene_fold_property(
            "Protein length (aa)",
            gene_item["protein_length_aa"],
            dark,
        ),
        _gene_fold_property(
            "Protein mass (kDa)",
            gene_item["protein_mass_kda"],
            dark,
        ),
        _gene_fold_property(
            "Disorder (%)",
            gene_item["disorder_pct"],
            dark,
        ),
        _gene_fold_property(
            "Isoelectric point (pI)",
            gene_item["isoelectric_point_pI"],
            dark,
        ),
        _gene_fold_property(
            "GRAVY score",
            gene_item["gravy_score"],
            dark,
        ),
        style=section_style,
    )

    return rx.el.div(
        _gene_fold_item(
            "mechanism",
            "Biological mechanism",
            "dna",
            mechanism_content,
            dark,
        ),
        _gene_fold_item(
            "evidence",
            "Experimental evidence",
            "flask",
            evidence_content,
            dark,
        ),
        rx.cond(
            has_organizations,
            _gene_fold_item(
                "organizations",
                "Labs & therapies",
                "building",
                organizations_content,
                dark,
            ),
            rx.fragment(),
        ),
        rx.cond(
            has_structure,
            _gene_fold_item(
                "structure",
                "Protein & printable STL",
                "cube",
                structure_content,
                dark,
            ),
            rx.fragment(),
        ),
        class_name="me-gene-details",
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "7px",
            "marginTop": "12px",
            "paddingTop": "12px",
            "borderTop": (
                "1px solid rgba(148, 163, 184, 0.18)"
                if dark
                else "1px solid #f3f4f6"
            ),
        },
    )


def _rpg_gene_card(gene_item: rx.Var) -> rx.Component:
    gene_sym = gene_item["gene"]
    gene_category = gene_item["category"]
    included = ComposeState.included_genes.contains(gene_sym)
    gene_price = gene_item["price"].to(int)
    cannot_afford = rx.cond(included, False, gene_price > ComposeState.budget_remaining)

    return rx.el.div(
        rx.el.div(
            rx.cond(
                included,
                rx.el.button(
                    "REMOVE",
                    on_click=ComposeState.toggle_gene_from_library(gene_sym, gene_category),
                    title="Remove gene",
                    style={
                        "width": "92px",
                        "minHeight": "40px",
                        "padding": "9px 12px",
                        "borderRadius": "8px",
                        "border": "1px solid rgba(248, 113, 113, 0.48)",
                        "background": "rgba(127, 29, 29, 0.34)",
                        "color": "#fecaca",
                        "fontSize": "0.78rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.08em",
                        "cursor": "pointer",
                        "flexShrink": "0",
                    },
                ),
                rx.el.button(
                    "ADD",
                    disabled=cannot_afford,
                    on_click=ComposeState.toggle_gene_from_library(gene_sym, gene_category),
                    title=rx.cond(cannot_afford, "Not enough enhancement credits", "Add gene"),
                    style={
                        "width": "92px",
                        "minHeight": "40px",
                        "padding": "9px 12px",
                        "borderRadius": "8px",
                        "border": rx.cond(cannot_afford, "1px solid rgba(248, 113, 113, 0.42)", "1px solid rgba(167, 139, 250, 0.58)"),
                        "background": rx.cond(cannot_afford, "rgba(127, 29, 29, 0.22)", "linear-gradient(135deg, #7c3aed, #6d28d9)"),
                        "color": rx.cond(cannot_afford, "#fca5a5", "#ffffff"),
                        "fontSize": "0.82rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.1em",
                        "cursor": rx.cond(cannot_afford, "not-allowed", "pointer"),
                        "opacity": rx.cond(cannot_afford, "0.72", "1"),
                        "flexShrink": "0",
                    },
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.cond(
                            gene_item["gene_url"] != "",
                            rx.el.a(
                                gene_sym,
                                href=gene_item["gene_url"],
                                target="_blank",
                                rel="noopener noreferrer",
                                title="Open in UniProt",
                                style={
                                    "fontSize": "0.96rem",
                                    "fontWeight": "900",
                                    "color": rx.cond(included, "#f8fafc", "#cbd5e1"),
                                    "textDecoration": "none",
                                    "borderBottom": "1px dotted rgba(124, 58, 237, 0.5)",
                                    "_hover": {"color": "#a78bfa", "borderBottomColor": "#a78bfa"},
                                },
                            ),
                            rx.el.span(
                                gene_sym,
                                style={
                                    "fontSize": "0.96rem",
                                    "fontWeight": "900",
                                    "color": rx.cond(included, "#f8fafc", "#cbd5e1"),
                                },
                            ),
                        ),
                        _confidence_signal_bars(gene_item["confidence_primary"]["value"]),
                        _manipulation_badge_dark(gene_item),
                        rx.el.span(
                            gene_item["price"],
                            " cr",
                            style={
                                "fontSize": "0.9rem",
                                "fontWeight": "900",
                                "padding": "4px 10px",
                                "borderRadius": "6px",
                                "backgroundColor": rx.cond(included, "rgba(124, 58, 237, 0.24)", "rgba(148, 163, 184, 0.12)"),
                                "color": rx.cond(cannot_afford, "#fca5a5", "#c4b5fd"),
                                "whiteSpace": "nowrap",
                            },
                        ),
                        style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "gap": "10px"},
                    ),
                    rx.el.div(
                        gene_item["category_detail"],
                        style={
                            "fontSize": "0.82rem",
                            "fontWeight": "700",
                            "color": _gene_category_accent_color(gene_category),
                            "marginTop": "2px",
                        },
                    ),
                    _secondary_categories_row(gene_item),
                    _rpg_gene_species_label(gene_item),
                    rx.el.div(
                        _gene_protein_id_row(gene_item, True),
                        style={"marginTop": "6px"},
                    ),
                    style={"flex": "1", "minWidth": "0"},
                ),
                style={
                    "flex": "1",
                    "minWidth": "0",
                },
            ),
            style={"display": "flex", "alignItems": "flex-start", "gap": "6px"},
        ),
        rx.el.div(
            rx.el.p(
                rx.foreach(gene_item["short_description_segments"], _gene_prose_segment),
                style={
                    "fontSize": "0.98rem",
                    "color": rx.cond(included, "#e0f2fe", "#dbeafe"),
                    "margin": "0",
                    "lineHeight": "1.62",
                    "whiteSpace": "pre-wrap",
                },
            ),
            rx.el.div(
                _gene_confidence_section(gene_item["confidence_primary"]),
                _gene_evidence_tier_row(gene_item["evidence_tier"]),
                _gene_availability_badges(gene_item),
                _gene_ai_controls(gene_item, dark=True),
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "6px",
                    "marginTop": "10px",
                },
            ),
            _gene_information_folds(gene_item, dark=True),
            class_name="me-rpg-gene-body-grid",
            style={"margin": "10px 0 0 26px"},
        ),
        style={
            "padding": "12px 14px",
            "borderRadius": "8px",
            "borderTop": "1px solid rgba(148, 163, 184, 0.22)",
            "borderRight": "1px solid rgba(148, 163, 184, 0.22)",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.22)",
            "borderLeft": rx.cond(included, _gene_category_border_left(gene_category), "2px solid rgba(148, 163, 184, 0.18)"),
            "background": rx.cond(
                included,
                "linear-gradient(135deg, rgba(30, 41, 59, 0.94), rgba(30, 27, 75, 0.92))",
                "rgba(15, 23, 42, 0.72)",
            ),
            "boxShadow": rx.cond(included, "0 0 22px rgba(124, 58, 237, 0.26)", "none"),
            "opacity": rx.cond(cannot_afford, "0.55", "1"),
            "overflow": "hidden",
        },
        class_name="me-rpg-gene-card",
    )


def _foreach_included_catalog_gene(row_fn) -> rx.Component:
    """Render full rows only for genes included in the generated artifacts."""
    return rx.foreach(ComposeState.included_composition_gene_rows, row_fn)


def _rpg_category_gene_accordion(category: str) -> rx.Component:
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    icon_name = CATEGORY_ICONS.get(category, "star")
    tooltip = _category_tooltip(category)
    count = ComposeState.active_display_gene_counts[category]
    spent = ComposeState.active_display_category_prices[category]
    is_selected = ComposeState.selected_categories.contains(category)
    is_open = ComposeState.gene_library_open_category == category
    total_count = GAME_CATEGORY_DISPLAY_COUNTS.get(category, 0)

    gene_grid = rx.el.div(
        rx.foreach(
            ComposeState.gene_catalog_by_category[category],
            _rpg_gene_card,
        ),
        class_name="me-rpg-category-gene-grid",
        style={
            "display": "grid",
            "gridTemplateColumns": "minmax(0, 1fr)",
            "gap": "10px",
            "padding": "10px 0 2px 16px",
            "marginLeft": "10px",
            "borderLeft": f"1px solid {color}44",
        },
    )

    return rx.el.details(
        rx.el.summary(
            rx.el.div(
                rx.el.span(
                    fomantic_icon(icon_name, size=17, color=color),
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "width": "32px",
                        "height": "32px",
                        "borderRadius": "10px",
                        "backgroundColor": f"{color}22",
                        "border": f"1px solid {color}55",
                        "boxShadow": f"0 0 14px {color}22",
                    },
                ),
                rx.el.div(
                    rx.el.div(
                        category,
                        style={"fontSize": "1.12rem", "fontWeight": "900", "color": "#f8fafc"},
                    ),
                    rx.el.div(
                        count,
                        f"/{total_count} genes selected · ",
                        spent,
                        " cr",
                        style={"fontSize": "0.86rem", "color": "#94a3b8", "marginTop": "1px"},
                    ),
                    style={"flex": "1", "minWidth": "0", "marginLeft": "10px"},
                ),
                rx.el.span(
                    rx.cond(
                        is_open,
                        "Open",
                        rx.cond(is_selected, "Active", "Expand"),
                    ),
                    style={
                        "fontSize": "0.82rem",
                        "fontWeight": "900",
                        "letterSpacing": "0.08em",
                        "textTransform": "uppercase",
                        "padding": "3px 8px",
                        "borderRadius": "6px",
                        "backgroundColor": rx.cond(
                            is_open,
                            f"{color}33",
                            rx.cond(is_selected, f"{color}22", "rgba(148, 163, 184, 0.12)"),
                        ),
                        "color": rx.cond(is_open | is_selected, color, "#cbd5e1"),
                        "whiteSpace": "nowrap",
                    },
                ),
                rx.el.span(
                    fomantic_icon("chevron-right", size=13, color="#cbd5e1"),
                    class_name="me-rpg-accordion-chevron",
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "width": "26px",
                        "height": "26px",
                        "borderRadius": "999px",
                        "backgroundColor": "rgba(15, 23, 42, 0.42)",
                        "border": "1px solid rgba(148, 163, 184, 0.28)",
                        "transition": "transform 0.16s ease, background-color 0.16s ease",
                        "marginLeft": "4px",
                        "flexShrink": "0",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "gap": "8px", "width": "100%"},
            ),
            style={
                "cursor": "pointer",
                "listStyle": "none",
                "padding": "14px 16px",
                "borderRadius": "8px",
                "background": f"linear-gradient(135deg, {color}22, rgba(15, 23, 42, 0.9))",
                "border": f"1px solid {color}55",
                "boxShadow": f"0 0 18px {color}18",
                "outline": "none",
            },
            title=tooltip,
            aria_label=tooltip,
            # Own the open/close in state so gene cards unmount when collapsed.
            # prevent_default stops the native <details> toggle from fighting us.
            on_click=[
                ComposeState.toggle_gene_library_accordion(category),
                rx.prevent_default,
            ],
        ),
        # Mount gene cards only while this fold is open (selection stays in state).
        rx.cond(is_open, gene_grid, rx.fragment()),
        class_name="me-rpg-category-accordion",
        id=_category_anchor_id(category),
        open=is_open,
        style={
            "background": "transparent",
            "border": "none",
            "borderRadius": "8px",
            "boxShadow": "none",
            "color": "#e5e7eb",
            "marginBottom": "0",
            "padding": "0",
        },
    )


def _rpg_gene_library_anchor_script() -> rx.Component:
    return rx.script(
        """
        (() => {
            const installerVersion = "state-accordion-mount-2026-07-28";
            if (window.__meGeneLibraryAnchorsInstalled === installerVersion) return;
            window.__meGeneLibraryAnchorsInstalled = installerVersion;

            const geneLibraryHash = (href) => {
                if (!href) return "";
                const index = href.indexOf("#gene-library-");
                return index >= 0 ? href.slice(index) : "";
            };

            const scrollToCategory = (href) => {
                const hash = geneLibraryHash(href);
                if (!hash) return;
                const target = document.getElementById(hash.slice(1));
                if (!target) return;
                // Open state is owned by ComposeState (body-map / summary clicks).
                // This script only scrolls so the opened fold is in view.
                window.setTimeout(() => {
                    target.scrollIntoView({ behavior: "smooth", block: "start" });
                }, 50);
            };

            document.addEventListener("click", (event) => {
                const link = event.target.closest('a[href*="#gene-library-"]');
                if (!link) return;
                window.setTimeout(() => scrollToCategory(link.getAttribute("href")), 0);
            });
            window.addEventListener("hashchange", () => scrollToCategory(window.location.hash));
            window.setTimeout(() => scrollToCategory(window.location.hash), 0);
        })();
        """
    )


def _rpg_gene_library_title() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon("book open", size=15, color="#a78bfa"),
            rx.el.span(
                "Gene library",
                style={
                    "marginLeft": "8px",
                    "fontSize": "1.08rem",
                    "fontWeight": "900",
                    "letterSpacing": "0.08em",
                    "textTransform": "uppercase",
                    "color": "#f8fafc",
                },
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        rx.el.div(
            "Build your enhanced character from real genes. Tap a category to browse.",
            style={
                "fontSize": "0.98rem",
                "fontWeight": "800",
                "color": "#c4b5fd",
                "marginTop": "2px",
                "lineHeight": "1.35",
            },
        ),
        class_name="me-rpg-library-title",
        style={"marginBottom": "12px"},
    )


def _pdb_viewer_scripts() -> rx.Component:
    """Auto-initialize 3Dmol for mounted Details viewers and clean up on close."""
    return rx.fragment(
        rx.script(
            """
            (() => {
                const installerVersion = "lazy-structure-2026-08-05";
                if (window.__mePdbViewerInstalled === installerVersion) return;
                window.__mePdbViewerInstalled = installerVersion;

                const pdbCache = {};
                let libraryLoading = false;
                const is3DmolCanvasError = (err) => String((err && (err.stack || err.message)) || err || "").includes("OffscreenCanvas.transferToImageBitmap");
                window.addEventListener("error", (event) => {
                    if (is3DmolCanvasError(event.error || event.message)) {
                        event.preventDefault();
                    }
                });

                const cleanupViewer = (el, resetInit = true) => {
                    if (el.__me_viewer) {
                        try { el.__me_viewer.spin(false); } catch(_) {}
                        try { el.__me_viewer.clear(); } catch(_) {}
                        el.__me_viewer = null;
                    }
                    if (resetInit) delete el.dataset.pdbInit;
                };

                document.querySelectorAll(".me-pdb-viewer").forEach((el) => cleanupViewer(el));

                const isRenderable = (el) => {
                    if (!el.isConnected) return false;
                    const rect = el.getBoundingClientRect();
                    return rect.width >= 40 && rect.height >= 40;
                };

                const markUnavailable = (el) => {
                    cleanupViewer(el, false);
                    el.dataset.pdbInit = "failed";
                    el.style.height = "auto";
                    el.style.minHeight = "0";
                    el.style.background = "transparent";
                    el.style.border = "1px dashed rgba(148, 163, 184, 0.35)";
                    el.innerHTML = '<div style="padding:8px 10px;color:#94a3b8;font-size:0.82rem;">Structure unavailable</div>';
                };

                const initViewer = (el) => {
                    if (el.dataset.pdbInit) return;
                    const src = el.dataset.pdbSrc;
                    if (!src || typeof $3Dmol === "undefined") return;
                    if (!isRenderable(el)) return;
                    el.dataset.pdbInit = "1";
                    const fail = () => markUnavailable(el);
                    let viewer;
                    try {
                        viewer = $3Dmol.createViewer(el, {
                            backgroundColor: "0x0f172a",
                            antialias: false,
                            useWorker: false,
                        });
                    } catch (_) {
                        fail();
                        return;
                    }
                    el.__me_viewer = viewer;
                    const guardMethod = (methodName) => {
                        const original = viewer[methodName];
                        if (typeof original !== "function") return;
                        viewer[methodName] = function() {
                            try {
                                return original.apply(viewer, arguments);
                            } catch (err) {
                                if (is3DmolCanvasError(err)) {
                                    fail();
                                    return undefined;
                                }
                                throw err;
                            }
                        };
                    };
                    guardMethod("render");
                    guardMethod("resize");
                    guardMethod("show");
                    el.addEventListener("webglcontextlost", (e) => {
                        e.preventDefault();
                        try {
                            viewer.spin(false);
                        } catch (_) {
                            fail();
                        }
                    }, false);
                    const show = (pdb) => {
                        const text = String(pdb || "");
                        if (!text || (!text.includes("ATOM") && !text.includes("HETATM"))) {
                            fail();
                            return;
                        }
                        try {
                            viewer.addModel(pdb, "pdb");
                            viewer.setStyle({}, {cartoon: {color: "spectrum"}});
                            viewer.zoomTo();
                            viewer.render();
                        } catch (_) {
                            fail();
                        }
                    };
                    if (pdbCache[src]) { show(pdbCache[src]); }
                    else {
                        fetch(src).then((r) => {
                            if (!r.ok) throw new Error("pdb fetch failed");
                            return r.text();
                        }).then((pdb) => {
                            pdbCache[src] = pdb;
                            show(pdb);
                        }).catch(fail);
                    }
                };

                const initWithin = (root) => {
                    if (!root || root.nodeType !== 1) return;
                    const viewers = [];
                    const canInit = (el) => {
                        const fold = el.closest("details.me-gene-information-fold");
                        return !fold || fold.open;
                    };
                    if (
                        root.matches
                        && root.matches(".me-pdb-viewer:not([data-pdb-init])")
                        && canInit(root)
                    ) viewers.push(root);
                    if (root.querySelectorAll) {
                        root.querySelectorAll(".me-pdb-viewer:not([data-pdb-init])").forEach((el) => {
                            if (canInit(el)) viewers.push(el);
                        });
                    }
                    if (!viewers.length) return;
                    if (typeof $3Dmol === "undefined") {
                        if (!libraryLoading) {
                            libraryLoading = true;
                            const script = document.createElement("script");
                            script.src = "https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js";
                            script.async = true;
                            script.onload = () => {
                                libraryLoading = false;
                                initWithin(document.body);
                            };
                            script.onerror = () => {
                                libraryLoading = false;
                                viewers.forEach(markUnavailable);
                            };
                            document.head.appendChild(script);
                        }
                        return;
                    }
                    viewers.forEach(initViewer);
                };

                const tryInit = () => {
                    initWithin(document.body);
                    document.addEventListener("toggle", (event) => {
                        const fold = event.target;
                        if (
                            !fold.matches
                            || !fold.matches("details.me-gene-information-fold")
                        ) return;
                        if (fold.open) {
                            initWithin(fold);
                            return;
                        }
                        fold.querySelectorAll(".me-pdb-viewer").forEach((el) => {
                            cleanupViewer(el);
                        });
                    }, true);
                    const obs = new MutationObserver((mutations) => {
                        for (const m of mutations) {
                            for (const n of m.addedNodes) initWithin(n);
                            for (const n of m.removedNodes) {
                                if (n.nodeType !== 1) continue;
                                if (n.classList && n.classList.contains("me-pdb-viewer")) cleanupViewer(n);
                                else if (n.querySelectorAll) n.querySelectorAll(".me-pdb-viewer").forEach((el) => cleanupViewer(el));
                            }
                        }
                    });
                    obs.observe(document.body, {childList: true, subtree: true});
                };
                if (document.readyState === "loading") {
                    document.addEventListener("DOMContentLoaded", tryInit);
                } else {
                    tryInit();
                }
            })();
            """
        ),
    )


def _term_hint_script() -> rx.Component:
    """Wrap method words inside open Details folds. Hover on desktop, tap on mobile."""
    return rx.script(
        r"""
        (() => {
            const installerVersion = "term-hints-2026-08-24";
            if (window.__meTermHintsInstalled === installerVersion) return;
            window.__meTermHintsInstalled = installerVersion;

            const TERMS = {
                knockout: "Loss-of-function: the gene is disrupted so the protein is gone or inactive.",
                overexpression: "Extra copies or forced high expression of the gene.",
                AAV: "Adeno-associated virus. A common gene-therapy delivery vector.",
                mRNA: "Messenger RNA. A transient instruction to make the protein, not a DNA edit.",
            };
            const names = Object.keys(TERMS).sort((a, b) => b.length - a.length);
            const re = new RegExp("\\b(" + names.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")\\b", "gi");

            const wrapRoot = (root) => {
                if (!root || root.dataset.meTermsWrapped === "1") return;
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
                    acceptNode(node) {
                        const text = node.nodeValue || "";
                        re.lastIndex = 0;
                        if (!re.test(text)) return NodeFilter.FILTER_REJECT;
                        const parent = node.parentElement;
                        if (!parent || parent.closest("a, button, .me-term-hint, script, style")) {
                            return NodeFilter.FILTER_REJECT;
                        }
                        return NodeFilter.FILTER_ACCEPT;
                    },
                });
                const nodes = [];
                while (walker.nextNode()) nodes.push(walker.currentNode);
                for (const node of nodes) {
                    const text = node.nodeValue || "";
                    const frag = document.createDocumentFragment();
                    let last = 0;
                    re.lastIndex = 0;
                    let match = re.exec(text);
                    while (match) {
                        if (match.index > last) {
                            frag.appendChild(document.createTextNode(text.slice(last, match.index)));
                        }
                        const key = names.find((n) => n.toLowerCase() === match[0].toLowerCase()) || match[0];
                        const span = document.createElement("span");
                        span.className = "me-term-hint";
                        span.dataset.term = key;
                        span.dataset.def = TERMS[key] || "";
                        span.setAttribute("tabindex", "0");
                        span.setAttribute("role", "button");
                        span.textContent = match[0];
                        frag.appendChild(span);
                        last = match.index + match[0].length;
                        match = re.exec(text);
                    }
                    if (last < text.length) {
                        frag.appendChild(document.createTextNode(text.slice(last)));
                    }
                    if (node.parentNode) node.parentNode.replaceChild(frag, node);
                }
                root.dataset.meTermsWrapped = "1";
            };

            const scan = () => {
                document.querySelectorAll(".me-gene-details").forEach(wrapRoot);
            };

            document.addEventListener("click", (event) => {
                const hint = event.target && event.target.closest ? event.target.closest(".me-term-hint") : null;
                document.querySelectorAll(".me-term-hint.is-open").forEach((el) => {
                    if (el !== hint) el.classList.remove("is-open");
                });
                if (!hint) return;
                hint.classList.toggle("is-open");
            });

            const observer = new MutationObserver(() => {
                window.requestAnimationFrame(scan);
            });
            observer.observe(document.body, { childList: true, subtree: true });
            scan();
        })();
        """
    )


def _rpg_gene_library_panel() -> rx.Component:
    return rx.el.div(
        _pdb_viewer_scripts(),
        _term_hint_script(),
        _rpg_gene_library_anchor_script(),
        _rpg_gene_library_title(),
        rx.el.div(_materialize_hint_bubble("genes"), style={"position": "relative"}),
        rx.el.div(
            *[_rpg_category_gene_accordion(cat) for cat in UNIQUE_CATEGORIES],
            class_name="me-rpg-library-grid",
        ),
        class_name="me-rpg-library-panel",
        style={**_RPG_PANEL_STYLE, "padding": "14px", "position": "relative"},
    )


def _materialization_info_item(icon_name: str, title: str, body: str | rx.Component) -> rx.Component:
    body_el = (
        rx.el.p(body, style={"color": "#cbd5e1", "fontSize": "0.9rem", "lineHeight": "1.55", "margin": "0"})
        if isinstance(body, str)
        else body
    )
    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=16, color="#a78bfa"),
            rx.el.strong(title, style={"marginLeft": "8px", "fontSize": "0.98rem"}),
            style={"display": "flex", "alignItems": "center", "marginBottom": "6px"},
        ),
        body_el,
        style={
            "padding": "12px",
            "borderRadius": "10px",
            "backgroundColor": "rgba(15, 23, 42, 0.56)",
            "border": "1px solid rgba(148, 163, 184, 0.22)",
        },
    )


def _materialization_support_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            fomantic_icon("print", size=18, color="#a78bfa"),
            rx.el.span(" 3D Printing Support", style={"marginLeft": "8px"}),
            style={"color": "#f8fafc", "display": "flex", "alignItems": "center", "margin": "0 0 12px"},
        ),
        rx.el.div(
            _materialization_info_item(
                "cube",
                "How to 3D print your sculpture",
                rx.el.p(
                    "Download the STL, open it in a slicer such as PrusaSlicer, Bambu Studio, Cura, or Lychee, "
                    "check the scale in millimeters, choose your material, add supports if your printer needs them, "
                    "then slice and print. The model is designed as a printable art object, but every printer and "
                    "material has its own tolerances. For optimal print profiles, see Marius Mihasan's ",
                    rx.el.a(
                        "3DP-Jmol printing profiles",
                        href="https://github.com/mariusmihasan/3DP-Jmol-3D-printing-profiles",
                        target="_blank",
                        rel="noopener noreferrer",
                        style={"color": "#a78bfa", "textDecoration": "underline"},
                    ),
                    " and his ",
                    rx.el.a(
                        "Modele Moleculare",
                        href="https://modelemoleculare.ro/",
                        target="_blank",
                        rel="noopener noreferrer",
                        style={"color": "#a78bfa", "textDecoration": "underline"},
                    ),
                    " project.",
                    style={"color": "#cbd5e1", "fontSize": "0.9rem", "lineHeight": "1.55", "margin": "0"},
                ),
            ),
            _materialization_info_item(
                "heart",
                "Support the project",
                "If you like the sculpture and report you generated, donations help us keep improving the gene "
                "library, fabrication pipeline, and public installation.",
            ),
            _materialization_info_item(
                "shipping fast",
                "Need us to print it?",
                "We can 3D print your generated sculpture and ship it inside the EU. Other countries are not "
                "supported yet, but we are working on expanding fulfilment.",
            ),
            _materialization_info_item(
                "industry",
                "Printing-company partnerships",
                "If you run a 3D printing company, partner with us so visitors can choose you as a local print "
                "option in their country.",
            ),
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
                "gap": "12px",
                "marginBottom": "14px",
            },
        ),
        rx.el.div(
            rx.el.a(
                rx.el.img(
                    src="/images/kofi.jpg",
                    alt="Ko-fi QR code - support Materialized Enhancements",
                    loading="lazy",
                    decoding="async",
                    style={
                        "width": "170px",
                        "height": "170px",
                        "display": "block",
                        "borderRadius": "8px",
                        "margin": "0 auto 8px auto",
                        "boxShadow": "0 2px 10px rgba(0,0,0,0.18)",
                    },
                ),
                rx.el.strong("Donate on Ko-fi", style={"display": "block", "textAlign": "center"}),
                rx.el.span(
                    "https://ko-fi.com/liviazaharia",
                    style={
                        "display": "block",
                        "color": "#c4b5fd",
                        "fontSize": "0.78rem",
                        "textAlign": "center",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "wordBreak": "break-all",
                        "marginTop": "4px",
                    },
                ),
                href="https://ko-fi.com/liviazaharia",
                target="_blank",
                rel="noopener noreferrer",
                style={
                    "flex": "1 1 220px",
                    "padding": "14px",
                    "borderRadius": "12px",
                    "backgroundColor": "rgba(124, 58, 237, 0.18)",
                    "border": "1px solid rgba(167, 139, 250, 0.34)",
                    "textDecoration": "none",
                },
            ),
            rx.el.div(
                rx.el.img(
                    src="/images/product.jpg",
                    alt="Product QR code - request a 3D-printed sculpture with EU delivery",
                    loading="lazy",
                    decoding="async",
                    style={
                        "width": "170px",
                        "height": "170px",
                        "display": "block",
                        "borderRadius": "8px",
                        "margin": "0 auto 8px auto",
                        "boxShadow": "0 2px 10px rgba(0,0,0,0.18)",
                    },
                ),
                rx.el.strong("Request print + delivery", style={"display": "block", "textAlign": "center"}),
                rx.el.span(
                    "Scan to request a finished sculpture shipped inside the EU.",
                    style={"display": "block", "color": "#cbd5e1", "fontSize": "0.82rem", "textAlign": "center", "marginTop": "4px"},
                ),
                rx.el.a(
                    "https://ko-fi.com/liviazaharia/shop",
                    href="https://ko-fi.com/liviazaharia/shop",
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "display": "block",
                        "color": "#c4b5fd",
                        "fontSize": "0.78rem",
                        "textAlign": "center",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "wordBreak": "break-all",
                        "marginTop": "4px",
                    },
                ),
                style={
                    "flex": "1 1 220px",
                    "padding": "14px",
                    "borderRadius": "12px",
                    "backgroundColor": "rgba(20, 83, 45, 0.22)",
                    "border": "1px solid rgba(34, 197, 94, 0.30)",
                },
            ),
            style={"display": "flex", "flexWrap": "wrap", "gap": "12px"},
        ),
        style={
            **_RPG_PANEL_STYLE,
            "padding": "14px",
            "marginTop": "0",
        },
    )


def _materialization_edit_character_cta() -> rx.Component:
    return rx.el.a(
        fomantic_icon("user edit", size=16, color="#ffffff"),
        rx.el.span(
            "Edit character",
            style={"marginLeft": "8px"},
        ),
        href="/",
        class_name="ui primary button",
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "marginBottom": "0",
            "padding": "11px 18px",
            "fontWeight": "900",
            "textDecoration": "none",
        },
    )


def _materialization_create_new_character_cta() -> rx.Component:
    return rx.el.button(
        fomantic_icon("user plus", size=16, color="#312e81"),
        rx.el.span(
            "Create new character",
            style={"marginLeft": "8px"},
        ),
        type="button",
        on_click=ComposeState.start_fresh,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "marginBottom": "0",
            "padding": "11px 18px",
            "borderRadius": "6px",
            "border": "1px solid rgba(196, 181, 253, 0.65)",
            "background": "#f8fafc",
            "color": "#312e81",
            "font": "inherit",
            "fontWeight": "900",
            "lineHeight": "1",
            "cursor": "pointer",
            "boxShadow": "0 8px 18px rgba(2, 6, 23, 0.18)",
        },
    )


def _post_materialization_action_card(
    icon_name: str,
    label: str,
    href: str,
    accent_color: str,
) -> rx.Component:
    return rx.el.a(
        rx.el.span(
            fomantic_icon(icon_name, size=22, color=accent_color),
            style={
                "width": "34px",
                "height": "34px",
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "borderRadius": "999px",
                "background": "rgba(255, 255, 255, 0.09)",
                "boxShadow": "inset 0 0 0 1px rgba(255, 255, 255, 0.10)",
                "flex": "0 0 auto",
            },
        ),
        rx.el.span(label, style={"marginLeft": "9px"}),
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        aria_label=label,
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "padding": "8px 14px 8px 9px",
            "boxSizing": "border-box",
            "minHeight": "46px",
            "minWidth": "0",
            "borderRadius": "999px",
            "background": "linear-gradient(135deg, rgba(124, 58, 237, 0.34), rgba(15, 23, 42, 0.68))",
            "border": "2px solid rgba(196, 181, 253, 0.34)",
            "color": "#e5e7eb",
            "fontSize": "0.96rem",
            "fontWeight": "900",
            "lineHeight": "1",
            "textDecoration": "none",
            "whiteSpace": "nowrap",
            "boxShadow": "0 8px 18px rgba(2, 6, 23, 0.20)",
        },
    )


def _materialization_post_generation_ctas() -> rx.Component:
    actions: list[rx.Component] = []
    if DISCORD_INVITE_URL:
        actions.append(
            _post_materialization_action_card(
                "discord",
                "Join Discord",
                DISCORD_INVITE_URL,
                "#a5b4fc",
            )
        )
    if GITHUB_PROJECT_URL:
        actions.append(
            _post_materialization_action_card(
                "comment",
                "Feature request",
                f"{GITHUB_PROJECT_URL.rstrip('/')}/issues",
                "#c4b5fd",
            )
        )
        actions.append(
            _post_materialization_action_card(
                "github",
                "Star GitHub",
                GITHUB_PROJECT_URL,
                "#e5e7eb",
            )
        )
    if DONATION_URL:
        actions.append(
            _post_materialization_action_card(
                "coffee",
                "Donate",
                DONATION_URL,
                "#f9a8d4",
            )
        )
    if not actions:
        return rx.fragment()
    return rx.el.div(
        *actions,
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "flexWrap": "wrap",
            "gap": "6px",
            "marginTop": "12px",
            "minWidth": "0",
        },
    )


def _reward_artifact_choice(
    label: str,
    description: str,
    icon_name: str,
    active: rx.Var,
    on_click: rx.EventSpec,
    action_label: str,
    image_src: str = "",
    image_alt: str = "",
    preview: rx.Component | None = None,
) -> rx.Component:
    """Compact clickable artifact selector shown inside the reward card."""
    if preview is None:
        preview = rx.el.img(
            src=image_src,
            alt=image_alt,
            loading="lazy",
            decoding="async",
            style={
                "width": "100%",
                "height": "100%",
                "objectFit": "contain",
                "objectPosition": "center",
                "display": "block",
                "filter": "saturate(1.08) contrast(1.04)",
            },
        )
    return rx.el.button(
        rx.el.div(
            rx.el.strong(label, style={"display": "block", "fontSize": "1.34rem", "lineHeight": "1.15"}),
            rx.el.span(description, style={"fontSize": "1.05rem", "lineHeight": "1.35", "color": rx.cond(active, "#dbeafe", "#cbd5e1")}),
            style={"minWidth": "0", "textAlign": "center", "padding": "4px 8px 0"},
        ),
        rx.el.div(
            preview,
            rx.el.div(
                fomantic_icon(icon_name, size=20, color="#ffffff"),
                style={
                    "position": "absolute",
                    "right": "10px",
                    "top": "10px",
                    "width": "36px",
                    "height": "36px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "borderRadius": "999px",
                    "background": "rgba(15, 23, 42, 0.78)",
                    "boxShadow": "0 8px 16px rgba(2, 6, 23, 0.28)",
                },
            ),
            style={
                "position": "relative",
                "width": "100%",
                "aspectRatio": "4 / 3",
                "maxHeight": "280px",
                "overflow": "hidden",
                "borderRadius": "14px",
                "background": "rgba(15, 23, 42, 0.72)",
                "border": rx.cond(active, "2px solid rgba(253, 230, 138, 0.95)", "1px solid rgba(196, 181, 253, 0.24)"),
            },
        ),
        rx.el.span(
            rx.cond(active, "Viewing now", action_label),
            rx.el.span(rx.cond(active, "", " ->"), style={"marginLeft": "7px"}),
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "alignSelf": "center",
                "minHeight": "38px",
                "padding": "9px 17px",
                "borderRadius": "999px",
                "background": rx.cond(active, "rgba(253, 230, 138, 0.96)", "rgba(255, 255, 255, 0.96)"),
                "color": rx.cond(active, "#422006", "#312e81"),
                "fontSize": "0.98rem",
                "fontWeight": "950",
                "lineHeight": "1",
                "boxShadow": "0 8px 18px rgba(2, 6, 23, 0.24)",
            },
        ),
        type="button",
        on_click=on_click,
        aria_label=action_label,
        class_name="me-reward-artifact-choice",
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
            "gap": "10px",
            "padding": "13px",
            "borderRadius": "20px",
            "border": rx.cond(active, "4px solid rgba(253, 230, 138, 0.92)", "3px solid rgba(196, 181, 253, 0.46)"),
            "background": rx.cond(
                active,
                "linear-gradient(135deg, rgba(124, 58, 237, 0.58), rgba(15, 23, 42, 0.78))",
                "linear-gradient(135deg, rgba(30, 41, 59, 0.82), rgba(15, 23, 42, 0.64))",
            ),
            "boxShadow": rx.cond(
                active,
                "0 0 0 4px rgba(124, 58, 237, 0.28), 0 18px 36px rgba(250, 204, 21, 0.18)",
                "0 12px 28px rgba(2, 6, 23, 0.22)",
            ),
            "color": "#f8fafc",
            "cursor": "pointer",
            "font": "inherit",
            "textAlign": "center",
            "appearance": "none",
            "width": "100%",
            "maxWidth": "none",
        },
    )


def _share_card_preview() -> rx.Component:
    """Social media icons preview for the Share & publish card."""
    icon_circle_style: dict = {
        "width": "54px",
        "height": "54px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "borderRadius": "999px",
        "border": "2px solid rgba(196, 181, 253, 0.38)",
        "boxShadow": "0 4px 18px rgba(124, 58, 237, 0.22)",
    }
    return rx.el.div(
        rx.el.div(
            fomantic_icon("twitter", size=26, color="#1DA1F2"),
            style={**icon_circle_style, "background": "rgba(29, 161, 242, 0.15)"},
        ),
        rx.el.div(
            fomantic_icon("facebook", size=26, color="#1877F2"),
            style={**icon_circle_style, "background": "rgba(24, 119, 242, 0.15)"},
        ),
        rx.el.div(
            fomantic_icon("linkedin", size=26, color="#0A66C2"),
            style={**icon_circle_style, "background": "rgba(10, 102, 194, 0.15)"},
        ),
        rx.el.div(
            fomantic_icon("linkify", size=26, color="#c4b5fd"),
            style={**icon_circle_style, "background": "rgba(196, 181, 253, 0.15)"},
        ),
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "gap": "18px",
            "width": "100%",
            "height": "100%",
            "background": "radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.18), rgba(15, 23, 42, 0.82) 70%)",
        },
    )


def _materialization_reward_panel() -> rx.Component:
    """Visitor-facing reward card for all generated materialization outputs."""
    model_active = ComposeState.materialization_artifact_tab == "model"
    report_active = ComposeState.materialization_artifact_tab == "report"
    share_active = ComposeState.materialization_artifact_tab == "share"
    return rx.cond(
        ComposeState.has_stl,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    fomantic_icon("trophy", size=34, color="#fde68a"),
                    style={
                        "width": "68px",
                        "height": "68px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "borderRadius": "999px",
                        "background": "radial-gradient(circle, rgba(250, 204, 21, 0.34), rgba(124, 58, 237, 0.20) 58%, rgba(15, 23, 42, 0.66))",
                        "border": "1px solid rgba(253, 230, 138, 0.48)",
                        "boxShadow": "0 0 0 5px rgba(124, 58, 237, 0.16), 0 0 34px rgba(250, 204, 21, 0.24)",
                        "flex": "0 0 auto",
                    },
                ),
                rx.el.div(
                    rx.el.span(
                        fomantic_icon("unlock alternate", size=13, color="#fde68a"),
                        rx.el.span(" Reward unlocked", style={"marginLeft": "6px"}),
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "width": "fit-content",
                            "padding": "6px 11px",
                            "borderRadius": "999px",
                            "background": "rgba(250, 204, 21, 0.16)",
                            "color": "#fde68a",
                            "fontSize": "0.82rem",
                            "fontWeight": "950",
                            "letterSpacing": "0.08em",
                            "textTransform": "uppercase",
                            "border": "1px solid rgba(253, 230, 138, 0.28)",
                        },
                    ),
                    rx.el.h2(
                        "Here is your reward: a 3D-printable crystal!",
                        style={
                            "margin": "10px 0 8px",
                            "color": "#f8fafc",
                            "fontSize": "clamp(1.45rem, 2.2vw, 2.15rem)",
                            "lineHeight": "1.08",
                            "fontWeight": "950",
                            "textShadow": "0 2px 18px rgba(124, 58, 237, 0.34)",
                        },
                    ),
                    rx.el.p(
                        "You also get a personal enhancement report from the genes you chose.",
                        style={
                            "margin": "0 0 14px 0",
                            "color": "#dbeafe",
                            "fontSize": "1.02rem",
                            "lineHeight": "1.5",
                            "maxWidth": "62rem",
                        },
                    ),
                    _profile_ai_panel(),
                    rx.el.p(
                        "Want a 3D-printed human or other goodies? "
                        "Not ready yet — comment on GitHub or donate to help us build it.",
                        style={
                            "margin": "0 auto",
                            "color": "#94a3b8",
                            "fontSize": "0.9rem",
                            "lineHeight": "1.4",
                            "maxWidth": "62rem",
                            "textAlign": "center",
                        },
                    ),
                    rx.el.div(
                        _materialization_post_generation_ctas(),
                        style={"marginTop": "4px"},
                    ),
                    style={"minWidth": "0", "flex": "1 1 560px"},
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                    "flexWrap": "wrap",
                },
            ),
            rx.el.div(
                _materialization_edit_character_cta(),
                rx.cond(
                    ComposeState.is_shared_visit,
                    _materialization_create_new_character_cta(),
                    rx.fragment(),
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "flexWrap": "wrap",
                    "gap": "8px",
                    "marginTop": "14px",
                },
            ),
            rx.el.div(
                _reward_artifact_choice(
                    "Printable crystal",
                    "Abstract form from your genes — not a body figure yet.",
                    "cube",
                    model_active,
                    ComposeState.show_model_artifact_tab,
                    "Open model",
                    image_src="/images/icons/shapes.jpg",
                    image_alt="Printed Materialized Enhancements crystal forms",
                ),
                _reward_artifact_choice(
                    "Personal enhancement report",
                    "Ready to view and print.",
                    "file alternate",
                    report_active,
                    ComposeState.show_report_artifact_tab,
                    "Open report",
                    image_src="/images/icons/report_icon.jpeg",
                    image_alt="Personal enhancement report icon",
                ),
                _reward_artifact_choice(
                    "Share & publish",
                    "Share on social media!",
                    "share alternate",
                    share_active,
                    ComposeState.show_share_artifact_tab,
                    "Open sharing",
                    image_src="/images/icons/share.jpg",
                    image_alt="Share and publish icon",
                ),
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                    "gap": "16px",
                    "justifyContent": "stretch",
                    "alignItems": "stretch",
                    "marginTop": "16px",
                },
                class_name="me-reward-artifact-choice-grid",
            ),
            style={
                "position": "relative",
                "overflow": "hidden",
                "padding": "18px",
                "borderRadius": "18px",
                "background": (
                    "radial-gradient(circle at 5% 8%, rgba(250, 204, 21, 0.24), transparent 24%), "
                    "linear-gradient(135deg, rgba(15, 23, 42, 0.86), rgba(76, 29, 149, 0.38))"
                ),
                "border": "1px solid rgba(253, 230, 138, 0.24)",
                "boxShadow": "0 18px 42px rgba(2, 6, 23, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.06)",
            },
        ),
        rx.fragment(),
    )


def _shared_report_banner() -> rx.Component:
    return rx.cond(
        ComposeState.has_loaded_shared_report,
        rx.el.div(
            rx.el.div(
                fomantic_icon("share alternate", size=18, color="#c4b5fd"),
                rx.el.div(
                    rx.el.strong("This materialization was shared with you.", style={"color": "#f8fafc"}),
                    rx.el.div(
                        "Explore the model and report below, then create your own character profile.",
                        style={"color": "#cbd5e1", "fontSize": "0.92rem", "marginTop": "2px"},
                    ),
                    style={"flex": "1", "minWidth": "220px"},
                ),
                rx.el.a(
                    "Create your own",
                    href="/",
                    class_name="ui primary button",
                    style={"textDecoration": "none", "fontWeight": "800"},
                ),
                style={"display": "flex", "alignItems": "center", "gap": "12px", "flexWrap": "wrap"},
            ),
            style={
                "padding": "14px",
                "border": "1px solid rgba(167, 139, 250, 0.38)",
                "borderRadius": "12px",
                "background": "linear-gradient(135deg, rgba(124, 58, 237, 0.22), rgba(15, 23, 42, 0.78))",
            },
        ),
        rx.cond(
            ComposeState.shared_report_error != "",
            _inline_notice(ComposeState.shared_report_error, size=16),
            rx.fragment(),
        ),
    )


def _model_artifact_preview() -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src="/images/icons/shapes.jpg",
            alt="Printed Materialized Enhancements 3D shapes",
            loading="lazy",
            decoding="async",
            style={
                "width": "100%",
                "height": "100%",
                "objectFit": "contain",
                "objectPosition": "center",
                "display": "block",
                "filter": "saturate(1.12) contrast(1.04)",
                "zIndex": "1",
            },
        ),
        rx.el.div(
            style={
                "position": "absolute",
                "inset": "0",
                "background": "radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.12), rgba(2, 6, 23, 0.00) 58%)",
                "pointerEvents": "none",
            },
        ),
        style={
            "position": "relative",
            "height": "clamp(240px, 24vw, 340px)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "overflow": "hidden",
            "borderRadius": "14px",
            "padding": "0",
            "background": "radial-gradient(circle at 50% 38%, rgba(124, 58, 237, 0.58), rgba(14, 165, 233, 0.20) 38%, rgba(2, 6, 23, 0.94) 76%)",
        },
    )


def _report_artifact_preview() -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src="/images/icons/report_icon.jpeg",
            alt="Personal enhancement report icon",
            loading="lazy",
            decoding="async",
            style={
                "width": "100%",
                "height": "100%",
                "objectFit": "cover",
                "objectPosition": "center",
                "display": "block",
                "filter": "saturate(1.08) contrast(1.04)",
                "zIndex": "1",
            },
        ),
        rx.el.div(
            style={
                "position": "absolute",
                "inset": "0",
                "background": "radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.12), rgba(2, 6, 23, 0.00) 58%)",
                "pointerEvents": "none",
            },
        ),
        style={
            "position": "relative",
            "height": "clamp(240px, 24vw, 340px)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "overflow": "hidden",
            "borderRadius": "14px",
            "padding": "0",
            "background": "radial-gradient(circle at 50% 40%, rgba(14, 165, 233, 0.34), rgba(124, 58, 237, 0.32) 44%, rgba(2, 6, 23, 0.94) 78%)",
        },
    )


def _jigsaw_artifact_preview() -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src="/puzzle/ALL_ANIMALS.svg",
            alt="Jigsaw organism pieces",
            loading="lazy",
            decoding="async",
            style={
                "height": "min(88%, 300px)",
                "maxWidth": "94%",
                "objectFit": "contain",
                "filter": "drop-shadow(0 18px 28px rgba(15, 23, 42, 0.42))",
            },
        ),
        style={
            "height": "clamp(240px, 24vw, 340px)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "overflow": "hidden",
            "borderRadius": "14px",
            "background": "radial-gradient(circle at 50% 42%, rgba(34, 197, 94, 0.24), rgba(124, 58, 237, 0.28) 44%, rgba(2, 6, 23, 0.94) 78%)",
        },
    )


def _support_artifact_preview() -> rx.Component:
    return rx.el.div(
        rx.el.img(
            src="/images/kofi.jpg",
            alt="Ko-fi donation QR code",
            loading="lazy",
            decoding="async",
            style={
                "width": "min(42%, 160px)",
                "aspectRatio": "1 / 1",
                "borderRadius": "18px",
                "boxShadow": "0 16px 32px rgba(15, 23, 42, 0.38)",
                "transform": "rotate(-4deg)",
            },
        ),
        rx.el.img(
            src="/images/product.jpg",
            alt="Print and delivery QR code",
            loading="lazy",
            decoding="async",
            style={
                "width": "min(42%, 160px)",
                "aspectRatio": "1 / 1",
                "borderRadius": "18px",
                "boxShadow": "0 16px 32px rgba(15, 23, 42, 0.38)",
                "transform": "rotate(5deg)",
                "marginLeft": "-26px",
                "marginTop": "56px",
            },
        ),
        style={
            "height": "clamp(240px, 24vw, 340px)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "overflow": "hidden",
            "borderRadius": "14px",
            "background": "radial-gradient(circle at 50% 42%, rgba(245, 158, 11, 0.30), rgba(124, 58, 237, 0.28) 44%, rgba(2, 6, 23, 0.94) 78%)",
        },
    )


def _artifact_tab_button(
    label: str,
    subtitle: str,
    icon_name: str,
    preview: rx.Component,
    badge: rx.Component,
    active: rx.Var,
    on_click: rx.EventSpec,
) -> rx.Component:
    """Large inventory card for an output artifact."""
    return rx.el.button(
        preview,
        rx.el.div(
            rx.el.div(
                fomantic_icon(icon_name, size=24, color=rx.cond(active, "#f8fafc", "#a78bfa")),
                rx.el.span(
                    label,
                    style={
                        "fontSize": "1.18rem",
                        "fontWeight": "950",
                        "letterSpacing": "0.01em",
                    },
                ),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "gap": "10px",
                    "minWidth": "0",
                    "textAlign": "center",
                },
            ),
            badge,
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "gap": "10px",
                "marginTop": "16px",
                "flexWrap": "wrap",
            },
        ),
        rx.el.p(
            subtitle,
            style={
                "margin": "8px auto 0",
                "fontSize": "0.92rem",
                "lineHeight": "1.45",
                "color": rx.cond(active, "#dbeafe", "#94a3b8"),
                "textAlign": "center",
                "maxWidth": "28rem",
            },
        ),
        type="button",
        on_click=on_click,
        style={
            "minWidth": "0",
            "boxSizing": "border-box",
            "padding": "8px",
            "borderRadius": rx.cond(active, "20px 20px 0 0", "20px"),
            "border": "0",
            "background": rx.cond(
                active,
                "linear-gradient(180deg, rgba(39, 48, 78, 0.98), rgba(15, 23, 42, 0.98))",
                "linear-gradient(180deg, rgba(30, 41, 59, 0.64), rgba(15, 23, 42, 0.62))",
            ),
            "color": rx.cond(active, "#f8fafc", "#cbd5e1"),
            "cursor": "pointer",
            "textAlign": "center",
            "appearance": "none",
            "font": "inherit",
            "boxShadow": rx.cond(
                active,
                (
                    "inset 4px 0 0 rgba(196, 181, 253, 0.95), "
                    "inset 0 4px 0 rgba(196, 181, 253, 0.95), "
                    "0 24px 48px rgba(124, 58, 237, 0.22)"
                ),
                "none",
            ),
            "opacity": rx.cond(active, "1", "0.86"),
            "transform": "none",
            "zIndex": rx.cond(active, "2", "1"),
        },
    )


def _jigsaw_artifact_placeholder() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon("puzzle piece", size=30, color="#c4b5fd"),
            rx.el.div(
                rx.el.h3("Jigsaw artifact", style={"margin": "0 0 4px 0", "color": "#f8fafc"}),
                rx.el.p(
                    "The jigsaw view is reserved for the future organism-piece artifact. "
                    "Keeping it in the inventory now makes room without adding another vertical accordion.",
                    style={"margin": "0", "color": "#cbd5e1", "lineHeight": "1.5"},
                ),
                style={"minWidth": "0"},
            ),
            style={"display": "flex", "alignItems": "center", "gap": "14px", "flexWrap": "wrap"},
        ),
        style={
            "padding": "26px",
            "borderRadius": "12px",
            "border": "1px dashed rgba(167, 139, 250, 0.45)",
            "background": "rgba(15, 23, 42, 0.54)",
        },
    )


def _artifact_tab_wrapper(tab_key: str, content: rx.Component) -> rx.Component:
    """Wrap a tab panel so it stays mounted but hidden when inactive.

    JS (QR painter, report views) modifies DOM inside these panels via
    innerHTML. Using rx.match to swap panels causes React removeChild
    errors because React tries to unmount nodes that JS already replaced.
    Keeping all panels mounted and toggling display avoids this.
    """
    return rx.el.div(
        content,
        style={
            "display": rx.cond(
                ComposeState.materialization_artifact_tab == tab_key,
                "block",
                "none",
            ),
        },
    )


def _artifact_inventory_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _artifact_tab_wrapper("model", _sculpture_section_body()),
            _artifact_tab_wrapper("report", _report_section_body()),
            _artifact_tab_wrapper("share", _share_section_body()),
            class_name="me-artifact-active-panel",
            style={
                "padding": "12px",
                "border": "4px solid rgba(253, 230, 138, 0.92)",
                "borderRadius": "20px",
                "background": "linear-gradient(135deg, rgba(124, 58, 237, 0.58), rgba(15, 23, 42, 0.78))",
                "boxShadow": "0 0 0 4px rgba(124, 58, 237, 0.28), 0 18px 36px rgba(250, 204, 21, 0.18)",
                "minWidth": "0",
            },
        ),
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "0",
            "borderRadius": "14px",
            "width": "100%",
            "minWidth": "0",
        },
    )

def _rpg_materialization_output() -> rx.Component:
    return rx.el.div(
        _pdb_viewer_scripts(),
        rx.el.textarea(
            value=ComposeState.stl_base64,
            id="stl-b64-data",
            style={"display": "none"},
        ),
        _report_capture_iframe(),
        _report_hidden_inputs(),
        _shared_report_banner(),
        _materialization_reward_panel(),
        _artifact_inventory_panel(),
        id="me-report-observer-root",
        class_name="me-rpg-output-panel",
        style={"display": "flex", "flexDirection": "column", "gap": "14px"},
    )


def _rpg_flow_css() -> rx.Component:
    return rx.el.style(
        """
        .me-rpg-shell {
            font-size: 16px;
        }
        @keyframes me-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes me-pulse {
            0% {
                transform: scale(1);
                filter: brightness(1);
                box-shadow: 0 0 24px rgba(124, 58, 237, 0.65), 0 10px 24px rgba(2, 6, 23, 0.38) !important;
            }
            50% {
                transform: scale(1.085);
                filter: brightness(1.28);
                box-shadow: 0 0 55px rgba(167, 139, 250, 0.95), 0 0 75px rgba(124, 58, 237, 0.72), 0 14px 34px rgba(2, 6, 23, 0.44) !important;
            }
            100% {
                transform: scale(1);
                filter: brightness(1);
                box-shadow: 0 0 24px rgba(124, 58, 237, 0.65), 0 10px 24px rgba(2, 6, 23, 0.38) !important;
            }
        }
        @keyframes me-pulse-border {
            0% {
                border-color: rgba(167, 139, 250, 0.42);
                box-shadow: 0 8px 30px rgba(124, 58, 237, 0.12);
            }
            50% {
                border-color: rgba(167, 139, 250, 0.72);
                box-shadow: 0 8px 35px rgba(124, 58, 237, 0.22);
            }
            100% {
                border-color: rgba(167, 139, 250, 0.42);
                box-shadow: 0 8px 30px rgba(124, 58, 237, 0.12);
            }
        }
        details.me-rpg-category-accordion > summary::-webkit-details-marker {
            display: none;
        }
        details.me-rpg-category-accordion > summary::marker {
            content: "";
        }
        details.me-gene-tested-on-fold > summary::-webkit-details-marker {
            display: none;
        }
        details.me-gene-tested-on-fold > summary::marker {
            content: "";
        }
        details.me-gene-tested-on-fold > summary::before {
            content: "▸";
            margin-right: 8px;
            color: #94a3b8;
            font-size: 0.85rem;
        }
        details.me-gene-tested-on-fold[open] > summary::before {
            content: "▾";
        }
        details.me-gene-information-fold > summary::-webkit-details-marker {
            display: none;
        }
        details.me-gene-information-fold > summary::marker {
            content: "";
        }
        details.me-gene-information-fold[open] > summary {
            background: rgba(124, 58, 237, 0.34) !important;
        }
        details.me-gene-information-fold[open] > summary .me-gene-fold-show {
            display: none;
        }
        details.me-gene-information-fold[open] > summary .me-gene-fold-hide {
            display: inline !important;
        }
        details.me-gene-information-fold[open] > summary .me-gene-fold-chevron {
            transform: rotate(180deg);
        }
        details.me-gene-information-fold[open] {
            box-shadow: 0 8px 20px rgba(2, 6, 23, 0.2) !important;
        }
        details.me-rpg-category-accordion[open] .me-rpg-accordion-chevron {
            transform: rotate(90deg);
        }
        .me-rpg-output-panel .ui.segment,
        .me-rpg-output-panel .ui.message {
            background: rgba(15, 23, 42, 0.72) !important;
            border-color: rgba(148, 163, 184, 0.26) !important;
            color: #e5e7eb !important;
        }
        .me-rpg-output-panel h3,
        .me-rpg-output-panel h4,
        .me-rpg-output-panel strong {
            color: #f8fafc !important;
        }
        .me-rpg-output-panel p,
        .me-rpg-output-panel span,
        .me-rpg-output-panel label,
        .me-rpg-output-panel div {
            border-color: rgba(148, 163, 184, 0.24);
        }
        .me-rpg-output-panel .me-artifact-active-panel {
            border: 4px solid rgba(253, 230, 138, 0.92) !important;
            border-radius: 20px !important;
            box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.28), 0 18px 36px rgba(250, 204, 21, 0.18) !important;
        }
        @media (hover: none) and (pointer: coarse) {
            .me-rpg-output-panel .me-reward-artifact-choice-grid {
                grid-template-columns: minmax(0, 1fr) !important;
                gap: 14px !important;
            }
            .me-rpg-output-panel .me-reward-artifact-choice {
                min-height: 0 !important;
                padding: 14px !important;
                gap: 12px !important;
            }
            .me-rpg-output-panel .me-reward-artifact-choice strong {
                font-size: 1.24rem !important;
                line-height: 1.18 !important;
                word-break: normal !important;
                overflow-wrap: normal !important;
            }
            .me-rpg-output-panel .me-reward-artifact-choice span {
                font-size: 0.98rem !important;
                line-height: 1.35 !important;
                word-break: normal !important;
                overflow-wrap: normal !important;
            }
            .me-rpg-output-panel .me-artifact-email-cell {
                flex: 1 1 100% !important;
                width: 100% !important;
                min-width: 0 !important;
                max-width: none !important;
            }
            .me-rpg-output-panel .me-email-send-form,
            .me-rpg-output-panel .me-email-send-row {
                width: 100% !important;
            }
            .me-rpg-output-panel .me-email-send-row {
                flex-direction: column !important;
                gap: 8px !important;
            }
            .me-rpg-output-panel .me-email-send-input {
                width: 100% !important;
                min-height: 46px !important;
                box-sizing: border-box !important;
                font-size: 1rem !important;
            }
            .me-rpg-output-panel .me-email-send-form .ui.button {
                width: 100% !important;
                min-height: 48px !important;
                justify-content: center !important;
                margin: 0 !important;
                white-space: normal !important;
                line-height: 1.2 !important;
            }
        }
        .me-rpg-dashboard {
            display: grid;
            gap: 16px;
            align-items: start;
            width: 100%;
        }
        .me-rpg-gene-body-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr);
            gap: 10px;
            align-items: start;
        }
        .me-rpg-hero-grid {
            display: flex;
            flex-wrap: nowrap;
            align-items: flex-start;
            min-height: 0;
            overflow-x: auto;
            overflow-y: hidden;
            scrollbar-width: thin;
        }
        .me-rpg-hero-grid > .me-rpg-left-panel {
            flex: 1.36 1 520px;
            min-width: min(100%, 420px);
        }
        .me-rpg-hero-grid > .me-rpg-center-panel {
            flex: 1.3 1 460px;
            min-width: min(100%, 320px);
            max-height: calc(100dvh - 7rem);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            scrollbar-width: thin;
            scrollbar-gutter: stable;
        }
        .me-rpg-hero-grid > .me-rpg-right-panel {
            flex: 0.46 1 220px;
            min-width: min(100%, 220px);
        }
        .me-rpg-profile-grid {
            grid-template-columns: minmax(320px, 0.82fr) minmax(0, 1.35fr);
        }
        .me-rpg-active-grid {
            grid-template-columns: minmax(320px, 0.68fr) minmax(0, 1.55fr);
        }
        .me-rpg-center-panel {
            min-width: 0;
        }
        .me-onboarding-center-lift {
            position: relative;
            z-index: 1010;
        }
        .me-onboarding-gene-lift .me-orientation-block,
        .me-onboarding-gene-lift .me-rpg-sidebar-intro,
        .me-onboarding-gene-lift .me-budget-gauge,
        .me-onboarding-gene-lift .me-rpg-library-title,
        .me-onboarding-gene-lift .me-rpg-library-grid {
            filter: blur(3px);
            opacity: 0.54;
            pointer-events: none;
            user-select: none;
        }
        .me-onboarding-gene-lift .me-onboarding-tip-card {
            filter: none;
            opacity: 1;
            pointer-events: auto;
            position: sticky;
            top: 0;
            z-index: 1210;
        }
        /* Short / capped left panels: keep step 1 tip pinned while the column scrolls. */
        .me-rpg-library-section.me-onboarding-gene-lift {
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            scrollbar-width: thin;
        }
        .me-onboarding-marker-hint {
            position: relative;
            z-index: 1010;
            pointer-events: none;
        }
        .me-onboarding-marker-hint .me-rpg-body-map-title,
        .me-onboarding-marker-hint .me-rpg-body-image,
        .me-onboarding-marker-hint .me-rpg-materialize-leg-cta {
            opacity: 0.18;
        }
        .me-onboarding-marker-hint .me-rpg-body-marker {
            opacity: 0.18;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .me-onboarding-marker-hint .me-rpg-body-marker--longevity-genome {
            z-index: 1010;
            opacity: 1;
            pointer-events: auto;
            filter: drop-shadow(0 0 18px rgba(124, 58, 237, 0.55));
            animation: me-onboarding-marker-pulse 2s ease-in-out infinite;
        }
        @keyframes me-onboarding-marker-pulse {
            0%, 100% { filter: drop-shadow(0 0 12px rgba(124, 58, 237, 0.4)); }
            50% { filter: drop-shadow(0 0 28px rgba(124, 58, 237, 0.75)); }
        }
        .me-budget-gauge {
            position: sticky;
            top: 0;
            z-index: 20;
            padding: 14px;
            border-radius: 12px 12px 12px 12px;
            background: rgba(15, 23, 42, 0.94);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(124, 58, 237, 0.32);
            box-shadow: 0 4px 20px rgba(2, 6, 23, 0.5);
            margin: 0 0 12px;
            width: 100%;
            box-sizing: border-box;
        }
        .me-rpg-sidebar-intro {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 12px;
        }
        .me-orientation-block {
            box-sizing: border-box;
            width: 100%;
            margin: 0 0 12px;
            padding: 14px 14px 12px;
            border-radius: 12px;
            border: 1px solid rgba(167, 139, 250, 0.32);
            background: rgba(15, 23, 42, 0.92);
            box-shadow: 0 8px 22px rgba(2, 6, 23, 0.36);
        }
        .me-orientation-headline {
            margin: 0 0 8px;
            color: #f8fafc;
            font-size: clamp(1.02rem, 2.4vw, 1.22rem);
            font-weight: 900;
            line-height: 1.35;
        }
        .me-orientation-body {
            margin: 0 0 8px;
            color: #cbd5e1;
            font-size: clamp(0.86rem, 2vw, 0.96rem);
            line-height: 1.5;
            font-weight: 600;
        }
        @media (max-width: 700px) {
            .me-orientation-block {
                padding: 10px 12px 8px;
            }
            .me-orientation-headline {
                margin-bottom: 6px;
                font-size: 1.02rem;
                line-height: 1.3;
            }
            .me-orientation-body {
                margin-bottom: 6px;
                font-size: 0.84rem;
                line-height: 1.4;
            }
            .me-orientation-help {
                min-height: 48px;
            }
        }
        .me-orientation-kb {
            margin: 8px 0 0;
            color: #94a3b8;
            font-size: 0.86rem;
            line-height: 1.45;
        }
        .me-orientation-help {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 48px;
            width: 100%;
            margin: 4px 0 0;
            padding: 10px 14px;
            border: 1px solid rgba(167, 139, 250, 0.55);
            border-radius: 10px;
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
            color: #f8fafc;
            font-size: 1.02rem;
            font-weight: 900;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            cursor: pointer;
        }
        .me-term-hint {
            position: relative;
            border-bottom: 1px dotted rgba(167, 139, 250, 0.75);
            cursor: help;
            color: inherit;
        }
        .me-term-hint::after {
            content: attr(data-def);
            position: absolute;
            left: 0;
            bottom: calc(100% + 8px);
            z-index: 40;
            width: min(280px, 72vw);
            padding: 8px 10px;
            border-radius: 8px;
            border: 1px solid rgba(167, 139, 250, 0.45);
            background: rgba(15, 23, 42, 0.96);
            color: #e2e8f0;
            font-size: 0.78rem;
            font-weight: 600;
            line-height: 1.4;
            opacity: 0;
            pointer-events: none;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.45);
        }
        @media (hover: hover) and (pointer: fine) {
            .me-term-hint:hover::after,
            .me-term-hint:focus-visible::after {
                opacity: 1;
            }
        }
        .me-term-hint.is-open::after {
            opacity: 1;
        }
        .me-rpg-body-map-panel {
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            min-height: 0;
            padding: 4px 0 0;
            color: #e5e7eb;
        }
        .me-rpg-body-map-title {
            max-width: 520px;
            margin: 0 auto 2px;
            padding: 10px 14px;
            border-radius: 14px;
            background: transparent;
            box-shadow: none;
            text-align: left;
        }
        .me-rpg-body-map-title > div {
            margin-bottom: 0 !important;
        }
        .me-rpg-body-stage {
            position: relative;
            width: 100%;
            min-height: clamp(620px, min(80dvh, 66vw), 900px);
            padding: 10px 26px 82px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow: visible;
            isolation: isolate;
        }
        .me-rpg-body-stage::before {
            content: "";
            position: absolute;
            inset: 3% 10% 2%;
            border-radius: 999px;
            background:
                radial-gradient(circle at 50% 38%, rgba(56, 189, 248, 0.32), rgba(56, 189, 248, 0.07) 33%, rgba(2, 6, 23, 0) 64%),
                radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.28), rgba(2, 6, 23, 0) 68%);
            filter: blur(18px);
            opacity: 0.94;
            pointer-events: none;
            z-index: 0;
        }
        .me-rpg-body-stage::after {
            content: "";
            position: absolute;
            inset: 18% 31% 8%;
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(248, 113, 113, 0.16), rgba(56, 189, 248, 0.13));
            filter: blur(30px);
            opacity: 0.75;
            pointer-events: none;
            z-index: 0;
        }
        .me-rpg-body-image {
            position: relative;
            z-index: 1;
            height: clamp(540px, min(74dvh, 60vw), 840px);
            max-width: min(100%, 760px);
            object-fit: contain;
            filter:
                blur(0.28px)
                drop-shadow(0 0 20px rgba(56, 189, 248, 0.48))
                drop-shadow(0 0 52px rgba(124, 58, 237, 0.34))
                drop-shadow(0 22px 42px rgba(2, 6, 23, 0.56));
            transform: translateZ(0);
            opacity: 0.96;
        }
        .me-rpg-body-marker {
            transition: transform 0.16s ease, filter 0.16s ease, opacity 0.16s ease;
        }
        .me-rpg-body-marker:hover {
            transform: translate(-50%, -50%) scale(1.06) !important;
            filter: brightness(1.12);
        }
        @media (prefers-reduced-motion: reduce), (hover: none) and (pointer: coarse), (max-width: 900px) {
            .me-rpg-body-stage::before,
            .me-rpg-body-stage::after {
                filter: none;
                opacity: 0.35;
            }
            .me-rpg-body-image {
                filter: drop-shadow(0 8px 16px rgba(2, 6, 23, 0.38));
                transform: none;
            }
            .me-rpg-gene-card img,
            .me-rpg-marker-gene-chip img {
                filter: invert(1) brightness(1.2) !important;
            }
            .me-mobile-body-change-overlay {
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }
        }
        .me-rpg-marker-icon-node i.icon {
            font-size: 60px !important;
            width: 1em !important;
            height: 1em !important;
            line-height: 1 !important;
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(1) {
            transform: translate(-50%, -50%) translate(0, -74px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(2) {
            transform: translate(-50%, -50%) translate(-64px, -58px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(3) {
            transform: translate(-50%, -50%) translate(64px, -58px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(4) {
            transform: translate(-50%, -50%) translate(-84px, -10px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(5) {
            transform: translate(-50%, -50%) translate(84px, -10px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(6) {
            transform: translate(-50%, -50%) translate(-36px, -86px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(7) {
            transform: translate(-50%, -50%) translate(36px, -86px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(8) {
            transform: translate(-50%, -50%) translate(0, -42px);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(1) .me-rpg-marker-gene-line {
            width: 52px;
            transform: rotate(-90deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(2) .me-rpg-marker-gene-line {
            width: 62px;
            transform: rotate(-138deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(3) .me-rpg-marker-gene-line {
            width: 62px;
            transform: rotate(-42deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(4) .me-rpg-marker-gene-line {
            width: 60px;
            transform: rotate(-173deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(5) .me-rpg-marker-gene-line {
            width: 60px;
            transform: rotate(-7deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(6) .me-rpg-marker-gene-line {
            width: 66px;
            transform: rotate(-113deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(7) .me-rpg-marker-gene-line {
            width: 66px;
            transform: rotate(-67deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(8) .me-rpg-marker-gene-line {
            width: 26px;
            transform: rotate(-90deg);
        }
        .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(n+9) {
            display: none;
        }
        .me-rpg-materialize-leg-cta {
            position: absolute;
            left: 50%;
            bottom: 12px;
            transform: translateX(-50%);
            z-index: 4;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 7px;
            pointer-events: auto;
        }
        .me-onboarding-materialize-lift {
            z-index: 6;
            border-radius: 30px;
            padding: 12px;
            background: rgba(15, 23, 42, 0.90);
            box-shadow: 0 0 35px rgba(255, 255, 255, 0.70);
        }
        .me-rpg-materialize-alert-stack {
            position: absolute;
            top: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .me-rpg-materialize-credit-line {
            padding: 5px 12px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(167, 139, 250, 0.42);
            color: #c4b5fd;
            font-size: 0.82rem;
            font-weight: 900;
            line-height: 1.1;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            box-shadow: 0 8px 22px rgba(2, 6, 23, 0.32);
        }
        .me-rpg-materialize-leg-button {
            appearance: none !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: min(82vw, 260px) !important;
            min-height: 58px !important;
            padding: 15px 26px !important;
            border: 0 !important;
            border-radius: 999px !important;
            background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 48%, #4c1d95 100%) !important;
            color: #ffffff !important;
            box-shadow:
                0 0 28px rgba(124, 58, 237, 0.62),
                0 12px 30px rgba(2, 6, 23, 0.38) !important;
            cursor: pointer !important;
            font-size: clamp(1.2rem, 2.3vw, 1.75rem) !important;
            font-weight: 950 !important;
            letter-spacing: 0.04em !important;
            line-height: 1 !important;
            text-transform: uppercase !important;
            white-space: nowrap !important;
            transition: transform 0.14s ease, filter 0.14s ease, box-shadow 0.14s ease !important;
        }
        .me-rpg-materialize-leg-button:hover:not(.is-disabled) {
            transform: translateY(-2px) scale(1.03);
            filter: brightness(1.08);
            box-shadow:
                0 0 38px rgba(124, 58, 237, 0.78),
                0 16px 38px rgba(2, 6, 23, 0.44) !important;
        }
        .me-rpg-materialize-leg-button.is-disabled {
            background: linear-gradient(135deg, #64748b 0%, #475569 100%) !important;
            box-shadow: 0 10px 26px rgba(2, 6, 23, 0.34) !important;
            cursor: not-allowed !important;
            opacity: 0.68 !important;
        }
        .me-rpg-materialize-leg-button.is-active-pulse {
            animation: me-pulse 2s infinite ease-in-out !important;
        }
        .me-mobile-body-change-overlay {
            display: none;
            opacity: 0;
            transform: translateY(18px) scale(0.96);
            transition: opacity 0.22s ease, transform 0.22s ease;
        }
        .me-mobile-body-change-mini-stage {
            position: relative;
            width: 118px;
            min-width: 118px;
            height: 138px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 16px;
            background:
                radial-gradient(circle at 50% 42%, rgba(56, 189, 248, 0.28), rgba(2, 6, 23, 0) 68%),
                rgba(2, 6, 23, 0.44);
            overflow: hidden;
        }
        .me-mobile-budget-materialize {
            display: none;
        }
        .me-mobile-budget-stack {
            display: block;
        }
        .me-rpg-category-anchor:hover {
            filter: brightness(1.12);
        }
        .me-rpg-trailer-link:hover {
            filter: brightness(1.12);
        }
        @media (min-width: 1500px) and (min-height: 900px) {
            .me-rpg-body-stage {
                min-height: clamp(720px, 82vh, 1040px);
            }
            .me-rpg-body-image {
                height: clamp(660px, 78vh, 980px);
                max-width: min(100%, 900px);
            }
        }
        @media (min-width: 1800px) and (min-height: 1050px) {
            .me-rpg-body-stage {
                min-height: clamp(820px, 84vh, 1160px);
            }
            .me-rpg-body-image {
                height: clamp(760px, 80vh, 1100px);
                max-width: min(100%, 1020px);
            }
        }
        .me-rpg-library-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }
        .me-rpg-library-section {
            height: calc(100vh - 7rem);
            max-height: calc(100vh - 7rem);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            padding: 12px 12px 20px 12px;
            box-sizing: border-box;
            scrollbar-width: thin;
            scrollbar-gutter: stable;
        }
        .me-rpg-left-panel,
        .me-rpg-right-panel {
            position: sticky;
            top: 16px;
            align-self: start;
        }
        @media (max-width: 1320px) {
            .me-rpg-hero-grid {
                align-items: stretch;
            }
            .me-rpg-right-panel {
                position: static !important;
            }
        }
        @media (max-width: 1100px) {
            .me-rpg-profile-grid,
            .me-rpg-active-grid {
                grid-template-columns: minmax(0, 1fr) !important;
            }
            .me-rpg-hero-grid {
                flex-wrap: nowrap;
                overflow-x: auto;
                overflow-y: hidden;
                align-items: stretch;
            }
            .me-rpg-hero-grid > .me-rpg-left-panel,
            .me-rpg-hero-grid > .me-rpg-center-panel,
            .me-rpg-hero-grid > .me-rpg-right-panel {
                flex-basis: auto;
            }
            .me-rpg-hero-grid > .me-rpg-left-panel {
                flex: 0 0 clamp(340px, 46vw, 420px);
                min-width: clamp(340px, 46vw, 420px);
            }
            .me-rpg-hero-grid > .me-rpg-center-panel {
                flex: 1 0 clamp(420px, 54vw, 620px);
                min-width: clamp(420px, 54vw, 620px);
                max-height: calc(100dvh - 6rem);
            }
            .me-rpg-library-section {
                height: calc(100dvh - 6rem);
                max-height: calc(100dvh - 6rem);
                overflow-y: auto;
                overflow-x: hidden;
                overscroll-behavior: contain;
                padding: 12px 12px 20px 12px;
                box-sizing: border-box;
            }
            .me-rpg-gene-body-grid {
                grid-template-columns: minmax(0, 1fr);
            }
            .me-rpg-category-gene-grid {
                grid-template-columns: minmax(0, 1fr) !important;
                padding-left: 0 !important;
                margin-left: 0 !important;
                border-left: none !important;
            }
            .me-rpg-body-map-panel {
                padding-top: 0;
            }
            .me-rpg-body-map-title {
                max-width: none;
            }
            .me-rpg-body-stage {
                min-height: clamp(600px, 92vw, 760px) !important;
                padding-left: 8px !important;
                padding-right: 8px !important;
                padding-bottom: 72px !important;
            }
            .me-rpg-body-image {
                height: clamp(520px, 88vw, 670px) !important;
                max-width: min(100%, 560px) !important;
            }
            .me-rpg-body-marker {
                transform: translate(-50%, -50%) scale(0.78) !important;
            }
            .me-rpg-body-marker:hover {
                transform: translate(-50%, -50%) scale(0.86) !important;
            }
            .me-rpg-materialize-leg-cta {
                bottom: 10px;
            }
            .me-rpg-materialize-leg-button {
                min-width: min(78vw, 230px) !important;
                min-height: 52px !important;
                padding: 13px 22px !important;
                font-size: clamp(1.05rem, 5.8vw, 1.45rem) !important;
            }
            .me-rpg-left-panel,
            .me-rpg-right-panel,
            .me-rpg-output-panel > div {
                position: static !important;
            }
        }
        @media (max-height: 820px) {
            .me-rpg-shell {
                min-height: calc(100dvh - 5.25rem) !important;
            }
            .me-rpg-hero-grid {
                align-items: stretch;
                max-height: calc(100dvh - 5.25rem);
            }
            .me-rpg-hero-grid > .me-rpg-center-panel {
                max-height: calc(100dvh - 5.25rem);
                padding-right: 4px;
            }
            .me-rpg-library-section {
                height: calc(100dvh - 5.25rem);
                max-height: calc(100dvh - 5.25rem);
            }
            .me-rpg-body-stage {
                min-height: clamp(620px, 82dvh, 760px) !important;
                padding: 4px 14px 96px !important;
            }
            .me-rpg-body-image {
                height: clamp(540px, 76dvh, 700px) !important;
                max-width: min(100%, 680px) !important;
            }
            .me-rpg-materialize-leg-cta {
                position: sticky;
                left: auto;
                bottom: 16px;
                transform: none;
                align-self: center;
                width: max-content;
                max-width: calc(100% - 24px);
                margin-top: 12px;
                margin-bottom: 10px;
            }
            .me-rpg-materialize-alert-stack {
                max-width: min(460px, 88vw);
            }
        }
        @media (min-width: 1200px) and (max-height: 900px) and (orientation: landscape) {
            .me-rpg-body-stage {
                min-height: clamp(600px, calc(100dvh - 13rem), 720px) !important;
                padding: 2px 14px 82px !important;
                justify-content: center !important;
            }
            .me-rpg-body-image {
                height: clamp(500px, calc(100dvh - 19rem), 620px) !important;
                max-width: min(100%, 720px) !important;
            }
            .me-rpg-materialize-leg-button {
                min-height: 54px !important;
                padding-top: 13px !important;
                padding-bottom: 13px !important;
            }
        }
        @media (orientation: portrait) and (min-width: 900px) {
            .me-rpg-body-stage {
                min-height: clamp(820px, min(84dvh, 92vw), 1180px) !important;
                padding: 0 18px 78px !important;
                justify-content: center !important;
            }
            .me-rpg-body-image {
                height: clamp(720px, min(76dvh, 72vw), 1040px) !important;
                max-width: min(100%, 920px) !important;
            }
            .me-rpg-body-marker--expression,
            .me-rpg-body-marker--perception {
                top: 23% !important;
            }
            .me-rpg-body-marker--longevity-genome,
            .me-rpg-body-marker--stress-resistance {
                top: 51% !important;
            }
            .me-rpg-body-marker--environmental-adaptation,
            .me-rpg-body-marker--regeneration {
                top: 70% !important;
            }
        }
        @media (min-width: 1800px) and (min-height: 1100px) {
            .me-rpg-body-stage {
                min-height: clamp(980px, 74dvh, 1160px) !important;
                padding-bottom: 112px !important;
            }
            .me-rpg-body-image {
                height: clamp(900px, 69dvh, 1080px) !important;
                max-width: min(100%, 1040px) !important;
            }
            .me-rpg-materialize-leg-button {
                min-width: 300px !important;
                min-height: 68px !important;
                font-size: clamp(1.6rem, 1.4vw, 2.05rem) !important;
            }
        }
        @media (max-width: 560px) {
            .me-rpg-shell {
                padding: 10px !important;
            }
            .me-rpg-dashboard {
                gap: 12px;
            }
            .me-rpg-body-map-title {
                padding: 9px 11px;
            }
            .me-rpg-body-stage {
                min-height: clamp(540px, 138vw, 680px) !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                padding-bottom: 62px !important;
            }
            .me-rpg-body-stage::before {
                inset: 8% 0 3%;
            }
            .me-rpg-body-stage::after {
                inset: 20% 20% 9%;
            }
            .me-rpg-body-image {
                height: clamp(430px, 116vw, 560px) !important;
                max-width: min(100%, 440px) !important;
                filter:
                    blur(0.22px)
                    drop-shadow(0 0 16px rgba(56, 189, 248, 0.42))
                    drop-shadow(0 0 38px rgba(124, 58, 237, 0.32))
                    drop-shadow(0 18px 34px rgba(2, 6, 23, 0.54));
            }
            .me-rpg-body-marker {
                transform: translate(-50%, -50%) scale(0.72) !important;
                width: 150px !important;
                height: 126px !important;
            }
            .me-rpg-body-marker:hover {
                transform: translate(-50%, -50%) scale(0.78) !important;
            }
            .me-rpg-body-marker--expression {
                top: 29% !important;
                left: 39% !important;
            }
            .me-rpg-body-marker--perception {
                top: 29% !important;
                left: 61% !important;
            }
            .me-rpg-body-marker--longevity-genome {
                top: 52% !important;
                left: 30% !important;
            }
            .me-rpg-body-marker--stress-resistance {
                top: 52% !important;
                left: 70% !important;
            }
            .me-rpg-body-marker--environmental-adaptation {
                top: 77% !important;
                left: 35% !important;
            }
            .me-rpg-body-marker--regeneration {
                top: 77% !important;
                left: 65% !important;
            }
            .me-rpg-marker-icon-node {
                width: 53px !important;
                height: 53px !important;
            }
            .me-rpg-marker-icon-node i.icon {
                font-size: 52px !important;
            }
            .me-rpg-marker-count-badge {
                min-width: 20px !important;
                height: 20px !important;
                font-size: 0.65rem !important;
            }
            .me-rpg-marker-gene-orbit {
                width: 150px !important;
                height: 126px !important;
            }
            .me-rpg-marker-gene-chip {
                width: 58px !important;
                min-height: 18px !important;
                font-size: 0.62rem !important;
                padding: 1px 4px !important;
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(1) {
                transform: translate(-50%, -50%) translate(0, -62px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(2) {
                transform: translate(-50%, -50%) translate(-54px, -46px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(3) {
                transform: translate(-50%, -50%) translate(54px, -46px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(4) {
                transform: translate(-50%, -50%) translate(-68px, -8px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(5) {
                transform: translate(-50%, -50%) translate(68px, -8px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(6) {
                transform: translate(-50%, -50%) translate(-28px, -72px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(7) {
                transform: translate(-50%, -50%) translate(28px, -72px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(8) {
                transform: translate(-50%, -50%) translate(0, -36px);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(1) .me-rpg-marker-gene-line {
                width: 42px;
                transform: rotate(-90deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(2) .me-rpg-marker-gene-line {
                width: 52px;
                transform: rotate(-140deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(3) .me-rpg-marker-gene-line {
                width: 52px;
                transform: rotate(-40deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(4) .me-rpg-marker-gene-line {
                width: 48px;
                transform: rotate(-173deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(5) .me-rpg-marker-gene-line {
                width: 48px;
                transform: rotate(-7deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(6) .me-rpg-marker-gene-line {
                width: 56px;
                transform: rotate(-111deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(7) .me-rpg-marker-gene-line {
                width: 56px;
                transform: rotate(-69deg);
            }
            .me-rpg-marker-gene-orbit .me-rpg-marker-gene-orbit-item:nth-child(8) .me-rpg-marker-gene-line {
                width: 22px;
                transform: rotate(-90deg);
            }
            .me-rpg-marker-label {
                top: calc(50% + 36px) !important;
                max-width: 230px !important;
                font-size: 0.98rem !important;
            }
            .me-rpg-marker-label span:first-child {
                font-size: 1.02rem !important;
            }
            .me-rpg-marker-category-full {
                font-size: 0.52rem !important;
            }
            .me-rpg-trailer-link {
                width: 58px !important;
                height: 58px !important;
            }
        }
        @media (hover: none) and (pointer: coarse) {
            .me-mobile-body-change-overlay {
                display: block;
            }
            .me-mobile-body-change-overlay.is-visible {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        .me-protein-stl-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
        }
        @media (min-width: 900px) {
            .me-protein-stl-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }
        }
        @media (min-width: 1400px) {
            .me-protein-stl-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        details.me-protein-stl-card > summary::-webkit-details-marker {
            display: none;
        }
        details.me-protein-stl-card > summary::marker {
            content: "";
        }
        details.me-protein-stl-card > summary {
            user-select: none;
        }
        details.me-protein-stl-card:hover > summary .me-protein-view3d-btn {
            background-color: rgba(167, 139, 250, 0.22) !important;
            border-color: rgba(167, 139, 250, 0.5) !important;
        }
        details.me-protein-stl-card[open] {
            border-color: rgba(167, 139, 250, 0.28) !important;
            background-color: rgba(15, 23, 42, 0.5) !important;
        }
        details.me-protein-stl-card[open] > summary .me-protein-view3d-btn {
            display: none;
        }
        """
    )


def _rpg_shell(content: rx.Component) -> rx.Component:
    return rx.el.div(
        _rpg_flow_css(),
        content,
        class_name="me-rpg-shell",
        style={
            "width": "100%",
            "padding": "16px",
            "borderRadius": "18px",
            "background": "linear-gradient(135deg, #020617 0%, #111827 48%, #1e1b4b 100%)",
            "boxSizing": "border-box",
            "minHeight": "calc(100vh - 7rem)",
        },
    )


def _rpg_character_profile_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.div(
                _rpg_body_map_panel(),
                class_name="me-rpg-center-panel",
            ),
            class_name="me-rpg-dashboard me-rpg-hero-grid",
        )
    )


def _onboarding_backdrop() -> rx.Component:
    return rx.cond(
        ComposeState.show_onboarding_suggestion,
        rx.el.div(
            on_click=ComposeState.advance_onboarding,
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100vw",
                "height": "100vh",
                "background": "rgba(2, 6, 23, 0.55)",
                "backdropFilter": "blur(3px)",
                "WebkitBackdropFilter": "blur(3px)",
                "zIndex": "1000",
                "cursor": "pointer",
                "pointerEvents": "auto",
            },
        ),
        rx.fragment(),
    )


def _rpg_active_genes_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.div(
                # Step 1 tip first so it is visible without scrolling past intro/video
                # on short viewports where the left panel is height-capped.
                _gene_library_onboarding_tooltip(),
                _orientation_block(),
                _rpg_sidebar_intro_stack(),
                _mobile_budget_materialize_stack(),
                _rpg_gene_library_panel(),
                id="gene-library",
                class_name=rx.cond(
                    ComposeState.show_onboarding_genes,
                    "me-rpg-left-panel me-rpg-library-section me-onboarding-gene-lift",
                    "me-rpg-left-panel me-rpg-library-section",
                ),
                style=rx.cond(
                    ComposeState.show_onboarding_genes,
                    {
                        "position": "relative",
                        "zIndex": "1200",
                        "pointerEvents": "none",
                    },
                    {},
                ),
            ),
            rx.el.div(
                _rpg_body_map_panel(),
                class_name=rx.cond(
                    ComposeState.show_onboarding_genes,
                    "me-rpg-center-panel me-onboarding-marker-hint",
                    rx.cond(
                        ComposeState.show_onboarding_center_lift,
                        "me-rpg-center-panel me-onboarding-center-lift",
                        "me-rpg-center-panel",
                    ),
                ),
            ),
            _onboarding_backdrop(),
            _mobile_body_change_overlay(),
            class_name="me-rpg-dashboard me-rpg-hero-grid",
            style=rx.cond(
                ComposeState.show_onboarding_suggestion,
                {"position": "relative", "isolation": "isolate"},
                {},
            ),
        )
    )


def _rpg_materialization_layout() -> rx.Component:
    return _rpg_shell(_rpg_materialization_output())


def _rpg_about_layout() -> rx.Component:
    return _rpg_shell(
        rx.el.div(
            rx.el.style(
                """
                #me-about-page h1,
                #me-about-page h2,
                #me-about-page h3,
                #me-about-page strong {
                    color: #f8fafc !important;
                }
                #me-about-page p,
                #me-about-page li {
                    color: #cbd5e1 !important;
                }
                #me-about-page a {
                    color: #c4b5fd !important;
                }
                #me-about-page .ui.primary.button {
                    color: #ffffff !important;
                }
                #me-about-page .me-about-layout {
                    display: grid;
                    grid-template-columns: minmax(0, 1fr);
                    gap: 18px;
                    align-items: start;
                    margin-bottom: 24px;
                }
                #me-about-page .me-about-main,
                #me-about-page .me-about-sidebar {
                    min-width: 0;
                }
                #me-about-page .me-about-sidebar {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                #me-about-page .me-about-support-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 12px;
                }
                @media (min-width: 1100px) {
                    #me-about-page .me-about-layout {
                        grid-template-columns: minmax(0, 1fr) minmax(440px, 600px);
                        gap: 24px;
                    }
                    #me-about-page .me-about-sidebar {
                        position: sticky;
                        top: 18px;
                    }
                }
                """
            ),
            _landing_tab(),
            id="me-about-page",
            style={**_RPG_PANEL_STYLE, "padding": "24px 18px"},
        )
    )


def _rpg_materialize_layout() -> rx.Component:
    return _rpg_active_genes_layout()


def _param_row(label: str, value: rx.Var, unit: str = "") -> rx.Component:
    """A single row in the sculpture parameters panel."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.78rem", "color": "#94a3b8", "flex": "0 0 74px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#64748b", "fontSize": "0.72rem"}),
            style={"fontSize": "0.82rem", "fontWeight": "800", "color": "#f8fafc"},
        ),
        style={"display": "flex", "alignItems": "center", "gap": "6px", "padding": "2px 0"},
    )


def _input_row(label: str, value: rx.Var, unit: str, arrow: bool = False) -> rx.Component:
    """Compact row: label + value + optional arrow connector."""
    return rx.el.div(
        rx.el.span(label, style={"fontSize": "0.78rem", "color": "#94a3b8", "flex": "0 0 84px"}),
        rx.el.span(
            value,
            rx.el.span(f" {unit}" if unit else "", style={"color": "#64748b", "fontSize": "0.72rem"}),
            style={"fontSize": "0.82rem", "fontWeight": "800", "color": "#f8fafc"},
        ),
        *(
            [rx.el.span(
                "\u2192",
                style={"fontSize": "0.78rem", "color": "#7c3aed", "fontWeight": "700", "marginLeft": "auto"},
            )] if arrow else []
        ),
        style={"display": "flex", "alignItems": "center", "gap": "5px", "padding": "2px 0"},
    )


def _explanation_item(term: str, desc: str, maps_to: str = "") -> rx.Component:
    """A single glossary entry in the explanations panel."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(term, style={"fontWeight": "800", "color": "#f8fafc", "fontSize": "0.82rem"}),
            *(
                [rx.el.span(
                    f"  {maps_to}",
                    style={"fontWeight": "800", "color": "#c4b5fd", "fontSize": "0.78rem", "marginLeft": "4px"},
                )] if maps_to else []
            ),
        ),
        rx.el.p(desc, style={"color": "#cbd5e1", "margin": "2px 0 0 0", "lineHeight": "1.35", "fontSize": "0.78rem"}),
        style={"padding": "7px 8px", "borderRadius": "8px", "background": "rgba(15, 23, 42, 0.46)"},
    )


def _explanations_panel() -> rx.Component:
    """Full-width glossary explaining how gene properties map to sculpture geometry."""
    return rx.cond(
        ComposeState.has_params,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    fomantic_icon("dna", size=14, color="#27ae60"),
                    rx.el.span(
                        "Name: ",
                        style={"fontWeight": "600", "color": "#94a3b8"},
                    ),
                    rx.el.span(
                        ComposeState.input_personal_tag,
                        style={"fontWeight": "800", "color": "#f8fafc", "fontSize": "0.9rem"},
                    ),
                    style={"display": "flex", "alignItems": "center", "gap": "4px"},
                ),
                rx.el.div(
                    rx.el.span("CRC32 ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_name_crc, style={"fontWeight": "600"}),
                    rx.el.span(" XOR mask ", style={"color": "#9ca3af"}),
                    rx.el.span(ComposeState.input_bitmask, style={"fontWeight": "600"}),
                    rx.el.span(" = seed ", style={"color": "#7c3aed"}),
                    rx.el.span(ComposeState.param_seed, style={"fontWeight": "700", "color": "#7c3aed"}),
                    style={"fontSize": "0.78rem", "color": "#e5e7eb"},
                ),
                style={
                    "display": "flex",
                    "gap": "10px",
                    "flexWrap": "wrap",
                    "alignItems": "center",
                    "padding": "8px",
                    "borderRadius": "8px",
                    "background": "rgba(15, 23, 42, 0.58)",
                },
            ),
            _explanation_item(
                "Gene pool",
                "selected genes with measured model data",
                maps_to="-> seed",
            ),
            _explanation_item(
                "Protein mass (kDa)",
                "median selected protein weight",
                maps_to="-> radius",
            ),
            _explanation_item(
                "Exon sum",
                "total coding segments across selected genes",
                maps_to="-> spacing",
            ),
            _explanation_item(
                "System size",
                "selected biological network size",
                maps_to="-> points",
            ),
            _explanation_item(
                "GRAVY score",
                "water/fat balance of selected proteins",
                maps_to="-> extrusion",
            ),
            _explanation_item(
                "Disorder %",
                "recorded for reproducibility; scale X stays print-safe",
                maps_to="recorded",
            ),
            _explanation_item(
                "Isoelectric point (pI)",
                "recorded for reproducibility; scale Y stays print-safe",
                maps_to="recorded",
            ),
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))",
                "gap": "6px",
                "padding": "8px",
                "borderRadius": "10px",
                "backgroundColor": "rgba(15, 23, 42, 0.56)",
                "border": "1px solid rgba(148, 163, 184, 0.24)",
                "marginBottom": "8px",
            },
        ),
        rx.fragment(),
    )


def _selected_model_values_panel() -> rx.Component:
    """User-selected values that feed the generated model."""
    return rx.el.div(
        rx.el.div(
            rx.el.span("Selected by visitor", style={"fontSize": "0.74rem", "fontWeight": "900", "color": "#c4b5fd", "letterSpacing": "0.07em", "textTransform": "uppercase"}),
            rx.el.span(
                ComposeState.export_categories_csv,
                style={"fontSize": "0.84rem", "color": "#f8fafc", "fontWeight": "800"},
            ),
            style={"display": "flex", "flexDirection": "column", "gap": "2px"},
        ),
        rx.el.div(
            rx.el.span(
                ComposeState.export_gene_names_csv,
                style={
                    "display": "block",
                    "fontSize": "0.82rem",
                    "lineHeight": "1.35",
                    "color": "#cbd5e1",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            ),
            style={"minWidth": "0"},
        ),
        style={
            "display": "grid",
            "gridTemplateColumns": "minmax(180px, 0.7fr) minmax(0, 1.3fr)",
            "gap": "10px",
            "alignItems": "center",
            "padding": "8px 10px",
            "borderRadius": "10px",
            "background": "rgba(20, 83, 45, 0.22)",
            "border": "1px solid rgba(34, 197, 94, 0.22)",
            "marginBottom": "8px",
        },
    )


def _gene_inputs_panel() -> rx.Component:
    """Compact panel: gene-derived quantitative inputs, ordered 1:1 with sculpture params."""
    return rx.el.div(
        rx.el.label(
            "Gene inputs",
            style={"fontSize": "0.8rem", "fontWeight": "800", "color": "#cbd5e1", "marginBottom": "4px", "display": "block"},
        ),
        rx.el.div(
            _input_row("Gene pool", ComposeState.param_pool_size, "genes", arrow=True),
            _input_row("Protein mass", ComposeState.input_mass_median, "kDa", arrow=True),
            _input_row("Exon sum", ComposeState.input_exon_sum, "", arrow=True),
            _input_row("System size", ComposeState.input_system_sum, "genes", arrow=True),
            _input_row("GRAVY score", ComposeState.input_gravy_median, "", arrow=True),
            _input_row("Disorder", ComposeState.input_disorder_median, "%", arrow=True),
            _input_row("Isoelectric pI", ComposeState.input_pi_median, "", arrow=True),
            style={
                "padding": "8px 10px",
                "borderRadius": "8px",
                "backgroundColor": "rgba(20, 83, 45, 0.24)",
                "border": "1px solid rgba(34, 197, 94, 0.32)",
            },
        ),
        style={"flex": "1", "minWidth": "0"},
    )


def _sculpture_params_panel() -> rx.Component:
    """Compact panel: computed sculpture geometry parameters."""
    return rx.el.div(
        rx.el.label(
            "3D model parameters",
            style={"fontSize": "0.8rem", "fontWeight": "800", "color": "#cbd5e1", "marginBottom": "4px", "display": "block"},
        ),
        rx.el.div(
            _param_row("Seed", ComposeState.param_seed),
            _param_row("Radius", ComposeState.param_radius, "mm"),
            _param_row("Spacing", ComposeState.param_spacing, "mm"),
            _param_row("Points", ComposeState.param_points),
            _param_row("Extrusion", ComposeState.param_extrusion),
            _param_row("Scale X", ComposeState.param_scale_x),
            _param_row("Scale Y", ComposeState.param_scale_y),
            style={
                "padding": "8px 10px",
                "borderRadius": "8px",
                "backgroundColor": "rgba(76, 29, 149, 0.25)",
                "border": "1px solid rgba(167, 139, 250, 0.32)",
            },
        ),
        style={"flex": "1", "minWidth": "0"},
    )


def _generation_story_metric(
    label: str,
    input_label: str,
    source_value: rx.Var,
    source_unit: str,
    result_label: str,
    output_value: rx.Var,
    output_unit: str,
    body: str,
) -> rx.Component:
    """Readable one-card explanation of one gene-property-to-geometry mapping."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(label, style={"fontSize": "0.78rem", "fontWeight": "900", "color": "#c4b5fd", "letterSpacing": "0.07em"}),
            rx.el.span(body, style={"fontSize": "0.78rem", "color": "#94a3b8", "marginLeft": "8px"}),
            style={"display": "flex", "alignItems": "baseline", "gap": "2px", "marginBottom": "4px"},
        ),
        rx.el.div(
            rx.el.span(input_label, style={"color": "#cbd5e1", "fontWeight": "800"}),
            rx.el.span(" ", style={"whiteSpace": "pre"}),
            rx.el.span(source_value, style={"fontWeight": "900", "color": "#f8fafc"}),
            rx.el.span(f" {source_unit}" if source_unit else "", style={"color": "#64748b"}),
            rx.el.span(" becomes ", style={"color": "#94a3b8", "padding": "0 6px"}),
            rx.el.span(result_label, style={"color": "#c4b5fd", "fontWeight": "800"}),
            rx.el.span(" ", style={"whiteSpace": "pre"}),
            rx.el.span(output_value, style={"fontWeight": "900", "color": "#f8fafc"}),
            rx.el.span(f" {output_unit}" if output_unit else "", style={"color": "#64748b"}),
            style={
                "fontSize": "0.86rem",
                "lineHeight": "1.35",
            },
        ),
        style={
            "padding": "8px 10px",
            "borderRadius": "8px",
            "background": "rgba(15, 23, 42, 0.62)",
        },
    )


def _model_generation_story_panel() -> rx.Component:
    """Plain-language generation explanation embedded in the model reward panel."""
    return rx.cond(
        ComposeState.has_params,
        rx.el.div(
            rx.el.div(
                fomantic_icon("magic", size=18, color="#c4b5fd"),
                rx.el.div(
                    rx.el.h3(
                        "How this crystal was generated",
                        style={
                            "margin": "0 0 6px 0",
                            "color": "#f8fafc",
                            "fontSize": "clamp(1.18rem, 1.8vw, 1.45rem)",
                            "lineHeight": "1.15",
                            "fontWeight": "950",
                        },
                    ),
                    rx.el.p(
                        "The app takes ",
                        rx.el.strong(ComposeState.param_pool_size, style={"color": "#ffffff"}),
                        " selected genes and grows a unique abstract crystal from their biophysical properties. "
                        "This is a printable souvenir of your choices — not a full-body figure "
                        "(that enhancement body model is still on the roadmap).",
                        style={
                            "margin": "0",
                            "fontSize": "1rem",
                            "lineHeight": "1.55",
                            "color": "#dbeafe",
                        },
                    ),
                    style={"minWidth": "0"},
                ),
                style={"display": "flex", "gap": "12px", "alignItems": "flex-start", "marginBottom": "12px"},
            ),
            rx.el.div(
                rx.el.span(
                    "Inputs: protein mass, exon count, biological system size, GRAVY score, disorder, pI, name, and categories.",
                    style={
                        "padding": "8px 10px",
                        "borderRadius": "999px",
                        "background": "rgba(15, 23, 42, 0.58)",
                        "color": "#cbd5e1",
                        "fontSize": "0.9rem",
                        "lineHeight": "1.35",
                    },
                ),
                rx.el.span(
                    "Outputs: seed, radius, layer spacing, Voronoi points, surface extrusion, and print-safe scale.",
                    style={
                        "padding": "8px 10px",
                        "borderRadius": "999px",
                        "background": "rgba(76, 29, 149, 0.28)",
                        "color": "#ddd6fe",
                        "fontSize": "0.9rem",
                        "lineHeight": "1.35",
                    },
                ),
                style={
                    "display": "flex",
                    "gap": "8px",
                    "flexWrap": "wrap",
                    "marginBottom": "10px",
                },
            ),
            rx.el.p(
                "Click the Model parameters accordion directly below to see the exact numbers and what each input controls.",
                style={
                    "margin": "0",
                    "fontSize": "0.92rem",
                    "lineHeight": "1.45",
                    "color": "#c4b5fd",
                    "fontWeight": "800",
                },
            ),
            style={
                "padding": "14px 16px",
                "borderRadius": "14px 14px 6px 6px",
                "background": "linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(76, 29, 149, 0.30))",
                "border": "1px solid rgba(196, 181, 253, 0.24)",
                "boxShadow": "0 16px 34px rgba(2, 6, 23, 0.22)",
            },
        ),
        rx.fragment(),
    )


def _section_header(
    expanded: rx.Var,
    icon_name: str,
    title: str,
    on_toggle: rx.EventSpec,
    right_badge: rx.Component = rx.fragment(),
) -> rx.Component:
    """Reusable collapsible section header."""
    return rx.el.div(
        rx.el.div(
            rx.cond(
                expanded,
                fomantic_icon("chevron-down", size=16, color="#7c3aed"),
                fomantic_icon("chevron-right", size=16, color="#7c3aed"),
            ),
            fomantic_icon(icon_name, size=16, color="#7c3aed", style={"marginLeft": "6px"}),
            rx.el.span(
                title,
                style={"fontSize": "1.05rem", "fontWeight": "600", "marginLeft": "8px"},
            ),
            style={"display": "flex", "alignItems": "center"},
        ),
        right_badge,
        on_click=on_toggle,
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "cursor": "pointer",
            "padding": "10px",
            "backgroundColor": "rgba(15, 23, 42, 0.72)",
            "borderRadius": "6px",
            "marginBottom": rx.cond(expanded, "10px", "0"),
            "color": "#f8fafc",
        },
    )


def _choice_section() -> rx.Component:
    """Collapsible: identity, selected genes, materialize button."""
    body = rx.cond(
        ComposeState.choice_expanded,
        rx.el.div(
            rx.el.label(
                "Your name",
                html_for="compose-personal-tag-materialize",
                style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
            ),
            _debounced_personal_tag_input(
                input_id="compose-personal-tag-materialize",
                style={
                    "width": "100%",
                    "padding": "10px 14px",
                    "borderRadius": "6px",
                    "border": "1px solid #d1d5db",
                    "fontSize": "0.95rem",
                    "marginBottom": "12px",
                    "outline": "none",
                    "backgroundColor": "#ffffff",
                    "color": "#1a1a2e",
                },
            ),
            rx.el.div(_materialize_hint_bubble("name"), style={"position": "relative"}),
            rx.cond(
                ComposeState.has_selection,
                rx.el.div(
                    rx.el.label(
                        "Selected categories:",
                        style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#4b5563", "marginBottom": "6px", "display": "block"},
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_categories, _selected_category_tag),
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2px", "marginBottom": "12px"},
                    ),
                    rx.el.div(class_name="ui divider"),
                    rx.el.label(
                        "Genes in selection",
                        style={
                            "fontSize": "0.95rem",
                            "fontWeight": "600",
                            "color": "#374151",
                            "display": "block",
                            "marginBottom": "8px",
                            "marginLeft": "22px",
                            "letterSpacing": "0.02em",
                        },
                    ),
                    rx.el.div(
                        rx.foreach(ComposeState.selected_gene_catalog, _gene_checkbox),
                        style={"display": "flex", "flexDirection": "column", "gap": "3px", "marginBottom": "12px"},
                    ),
                    rx.el.div(_materialize_hint_bubble("genes"), style={"position": "relative"}),
                ),
                rx.el.p(
                    "Select categories from the left panel.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
            rx.el.button(
                rx.cond(
                    ComposeState.generating,
                    fomantic_icon("sync", size=16, style={"animation": "me-spin 1s linear infinite"}),
                    fomantic_icon("atom", size=16),
                ),
                rx.el.span(
                    rx.cond(ComposeState.generating, " Generating\u2026", " Materialize"),
                    style={"marginLeft": "8px"},
                ),
                on_click=ComposeState.materialize,
                on_mouse_enter=ComposeState.show_materialize_hint,
                on_mouse_leave=ComposeState.hide_materialize_hint,
                class_name=rx.cond(
                    ComposeState.generating,
                    "ui disabled primary button",
                    rx.cond(ComposeState.can_materialize, "ui primary button", "ui disabled primary button"),
                ),
                style={"width": "100%", "padding": "12px", "fontSize": "1rem"},
            ),
            rx.el.style("@keyframes me-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.choice_expanded,
            icon_name="user",
            title="Choice",
            on_toggle=ComposeState.toggle_choice_expanded,
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


def _model_parameters_accordion() -> rx.Component:
    """Nested accordion with reproducible sculpture inputs and geometry parameters."""
    body = rx.cond(
        ComposeState.sculpture_expanded,
        rx.el.div(
            rx.cond(
                ComposeState.has_params,
                rx.el.div(
                    _selected_model_values_panel(),
                    _explanations_panel(),
                    rx.el.div(
                        _gene_inputs_panel(),
                        _sculpture_params_panel(),
                        style={
                            "display": "flex",
                            "gap": "8px",
                            "flexWrap": "wrap",
                            "marginBottom": "8px",
                        },
                    ),
                ),
                rx.el.p(
                    "Parameters will appear after selecting categories.",
                    style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
                ),
            ),
        ),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.sculpture_expanded,
            icon_name="sparkles",
            title="Model parameters",
            on_toggle=ComposeState.toggle_sculpture_expanded,
            right_badge=rx.cond(
                ComposeState.has_params,
                rx.el.span(
                    ComposeState.param_pool_size,
                    rx.el.span(" genes", style={"marginLeft": "2px"}),
                    class_name="ui mini violet label",
                    style={"fontSize": "0.74rem", "fontWeight": "800"},
                ),
                rx.fragment(),
            ),
        ),
        body,
        style={
            **_COLLAPSIBLE_STYLE,
            "backgroundColor": "rgba(15, 23, 42, 0.38)",
            "marginTop": "0",
            "marginBottom": "10px",
        },
    )


def _model_action_panel() -> rx.Component:
    compact_button_style = {
        "width": "100%",
        "padding": "14px 20px",
        "fontSize": "1.04rem",
        "fontWeight": "900",
        "whiteSpace": "nowrap",
    }
    action_cell_style = {
        "flex": "0 1 300px",
        "minWidth": "260px",
        "maxWidth": "340px",
    }

    return rx.el.div(
        rx.el.div(
            rx.el.strong(
                "Take your artifact with you",
                style={"display": "block", "fontSize": "1.12rem", "color": "#f8fafc", "marginBottom": "4px"},
            ),
            rx.el.span(
                "Download the 3D print file, or email the print file and report to yourself.",
                style={"display": "block", "fontSize": "0.94rem", "lineHeight": "1.45", "color": "#cbd5e1"},
            ),
            style={"marginBottom": "10px"},
        ),
        rx.el.div(
            rx.el.span(
                ComposeState.stl_filename,
                style={"fontSize": "0.78rem", "color": "#94a3b8", "wordBreak": "break-all"},
            ),
            style={"marginBottom": "8px"},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    fomantic_icon("download", size=14),
                    rx.el.span(" Download 3D print file", style={"marginLeft": "6px"}),
                    on_click=ComposeState.download_stl,
                    class_name="ui primary button",
                    style=compact_button_style,
                ),
                rx.el.button(
                    fomantic_icon("file code outline", size=14),
                    rx.el.span(" Download parameters", style={"marginLeft": "6px"}),
                    on_click=ComposeState.download_params_json,
                    class_name="ui button",
                    style={**compact_button_style, "marginTop": "6px", "fontWeight": "600"},
                ),
                style=action_cell_style,
            ),
            rx.el.div(
                _email_send_form(ComposeState, button_label="Send print file + report"),
                class_name="me-artifact-email-cell",
                style={
                    "flex": "1 1 440px",
                    "minWidth": "340px",
                    "maxWidth": "620px",
                },
            ),
            rx.cond(
                ComposeState.artex_section_visible,
                rx.el.div(
                    artex_publish_button(ComposeState, ComposeState.create_artex_project),
                    style=action_cell_style,
                ),
                rx.fragment(),
            ),
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "10px",
                "alignItems": "flex-start",
            },
        ),
        style={
            "padding": "12px",
            "borderRadius": "8px",
            "backgroundColor": "rgba(15, 23, 42, 0.46)",
            "marginTop": "10px",
            "marginBottom": "10px",
        },
    )


def _protein_stl_row(entry: dict) -> rx.Component:
    """Foldable card for a protein STL with embedded PDB viewer."""
    diff = entry["difficulty"]
    diff_color = rx.match(
        diff,
        ("easy", "#22c55e"),
        ("medium", "#eab308"),
        ("hard", "#f97316"),
        ("expert", "#ef4444"),
        "#9ca3af",
    )
    diff_icon = rx.match(
        diff,
        ("easy", "check circle"),
        ("medium", "info circle"),
        ("hard", "exclamation triangle"),
        ("expert", "warning sign"),
        "question circle",
    )
    has_structure = entry["structure_pdb"] != ""

    view_3d_btn = rx.cond(
        has_structure,
        rx.el.div(
            fomantic_icon("cube", size=11, color="#a78bfa"),
            rx.el.span(" View 3D", style={"fontSize": "0.76rem", "fontWeight": "700"}),
            class_name="me-protein-view3d-btn",
            style={
                "display": "inline-flex",
                "alignItems": "center",
                "gap": "3px",
                "color": "#c4b5fd",
                "padding": "3px 10px",
                "borderRadius": "5px",
                "border": "1px solid rgba(167, 139, 250, 0.35)",
                "backgroundColor": "rgba(167, 139, 250, 0.12)",
                "cursor": "pointer",
                "transition": "background-color 0.15s, border-color 0.15s",
            },
        ),
        rx.fragment(),
    )

    summary_row = rx.el.summary(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    entry["gene"],
                    style={"fontWeight": "700", "fontSize": "0.92rem", "color": "#f1f5f9"},
                ),
                rx.el.div(
                    fomantic_icon(diff_icon, size=12),
                    rx.el.span(diff, style={"fontSize": "0.74rem", "textTransform": "capitalize"}),
                    style={"color": diff_color, "display": "inline-flex", "alignItems": "center", "gap": "3px"},
                ),
                style={"display": "flex", "alignItems": "center", "gap": "8px"},
            ),
            rx.el.div(
                rx.el.span(
                    entry["source_label"],
                    style={"fontSize": "0.74rem", "color": "#94a3b8"},
                ),
                view_3d_btn,
                rx.el.button(
                    fomantic_icon("download", size=11),
                    rx.el.span(" STL", style={"fontSize": "0.72rem", "fontWeight": "600"}),
                    on_click=ComposeState.download_protein_stl(entry["gene"]),
                    class_name="ui mini icon button",
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "gap": "2px",
                        "padding": "3px 8px",
                        "background": "rgba(124, 58, 237, 0.2)",
                        "border": "1px solid rgba(124, 58, 237, 0.35)",
                        "color": "#c4b5fd",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "flexShrink": "0",
                    },
                ),
                style={"display": "flex", "alignItems": "center", "gap": "6px", "flexWrap": "wrap"},
            ),
            style={"display": "flex", "flexDirection": "column", "gap": "4px", "flex": "1", "minWidth": "0"},
        ),
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "padding": "8px 10px",
            "cursor": "pointer",
            "listStyle": "none",
        },
    )

    viewer_panel = rx.cond(
        has_structure,
        rx.el.div(
            rx.el.div(
                class_name="me-pdb-viewer",
                custom_attrs={"data-pdb-src": entry["pdb_src_url"]},
                style={
                    "width": "100%",
                    "height": "240px",
                    "borderRadius": "6px",
                    "border": "1px solid rgba(167, 139, 250, 0.28)",
                    "background": "#0f172a",
                    "position": "relative",
                    "overflow": "hidden",
                },
            ),
            rx.el.p(
                "Drag to rotate · Scroll to zoom",
                style={"fontSize": "0.7rem", "color": "#64748b", "textAlign": "center", "margin": "3px 0 0"},
            ),
            style={"padding": "6px 8px 4px"},
        ),
        rx.el.div(
            rx.el.span(
                "3D preview not available",
                style={"fontSize": "0.76rem", "color": "#64748b", "fontStyle": "italic"},
            ),
            style={"padding": "8px"},
        ),
    )

    detail_row = rx.el.div(
        rx.el.div(
            rx.el.span(
                entry["render_label"],
                style={
                    "fontSize": "0.68rem",
                    "fontWeight": "600",
                    "color": "#a78bfa",
                    "backgroundColor": "rgba(167, 139, 250, 0.12)",
                    "border": "1px solid rgba(167, 139, 250, 0.25)",
                    "borderRadius": "4px",
                    "padding": "1px 6px",
                    "marginRight": "6px",
                },
            ),
            rx.el.span(
                "Print size: " + entry["dimensions_mm"].to(str) + " mm",
                style={"fontSize": "0.72rem", "color": "#cbd5e1"},
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"},
        ),
        rx.el.div(
            rx.el.span(entry["triangles"].to(str) + " tris · " + entry["shells"].to(str) + " shells"),
            style={"fontSize": "0.72rem", "color": "#64748b"},
        ),
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "2px",
            "padding": "4px 9px 7px",
        },
    )

    return rx.el.details(
        summary_row,
        viewer_panel,
        detail_row,
        class_name="me-protein-stl-card",
        style={
            "borderRadius": "8px",
            "backgroundColor": "rgba(15, 23, 42, 0.35)",
            "border": "1px solid rgba(148, 163, 184, 0.1)",
            "overflow": "hidden",
        },
    )


def _protein_stl_panel() -> rx.Component:
    """Panel listing downloadable protein structure STLs for the selected genes."""
    return rx.cond(
        ComposeState.protein_stl_entries.length() > 0,
        rx.el.div(
            rx.el.div(
                fomantic_icon("dna", size=16),
                rx.el.span(
                    " Printable protein structures",
                    style={"fontWeight": "600", "fontSize": "1.05rem", "color": "#f8fafc"},
                ),
                style={"display": "flex", "alignItems": "center", "gap": "6px", "marginBottom": "6px"},
            ),
            rx.el.div(
                fomantic_icon("exclamation triangle", size=12),
                rx.el.span(
                    " You can also 3D print the individual protein structures included in your character. "
                    "All models are scaled to fit a 180mm print bed (e.g. Bambu A1 Mini). "
                    "Some may need mesh repair for best results. For optimized printing profiles, check Marius Mihasan's ",
                    rx.el.a(
                        "3DP-Jmol printing profiles",
                        href="https://github.com/mariusmihasan/3DP-Jmol-3D-printing-profiles",
                        target="_blank",
                        rel="noopener noreferrer",
                        style={"color": "#fbbf24", "textDecoration": "underline"},
                    ),
                    " and his ",
                    rx.el.a(
                        "Modele Moleculare",
                        href="https://modelemoleculare.ro/",
                        target="_blank",
                        rel="noopener noreferrer",
                        style={"color": "#fbbf24", "textDecoration": "underline"},
                    ),
                    " project.",
                    style={"fontSize": "0.84rem", "lineHeight": "1.45"},
                ),
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "gap": "6px",
                    "padding": "8px 10px",
                    "borderRadius": "6px",
                    "backgroundColor": "rgba(234, 179, 8, 0.12)",
                    "color": "#fbbf24",
                    "marginBottom": "10px",
                    "border": "1px solid rgba(234, 179, 8, 0.25)",
                },
            ),
            rx.el.div(
                rx.foreach(
                    ComposeState.protein_stl_entries,
                    _protein_stl_row,
                ),
                class_name="me-protein-stl-grid",
            ),
            style={
                "padding": "14px",
                "borderRadius": "10px",
                "backgroundColor": "rgba(15, 23, 42, 0.46)",
                "marginTop": "12px",
                "border": "1px solid rgba(124, 58, 237, 0.2)",
            },
        ),
        rx.fragment(),
    )


def _sculpture_section_body() -> rx.Component:
    """Printable model contents without the outer accordion header."""
    return rx.cond(
        ComposeState.has_stl,
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.iframe(
                        src=ComposeState.viewer_iframe_src,
                        id="sculpture-viewer-iframe",
                        style={
                            "width": "100%",
                            "height": "840px",
                            "border": "1px solid #e5e7eb",
                            "borderRadius": "8px",
                            "backgroundColor": "#1a1a2e",
                        },
                    ),
                    rx.el.p(
                        "Drag to rotate · Scroll to zoom · Right-drag to pan",
                        style={"fontSize": "0.82rem", "color": "#9ca3af", "textAlign": "center", "marginTop": "6px"},
                    ),
                    style={"flex": "1 1 620px", "minWidth": "0"},
                ),
                style={
                    "display": "flex",
                    "alignItems": "stretch",
                    "gap": "14px",
                    "flexWrap": "wrap",
                },
            ),
            _model_generation_story_panel(),
            _model_parameters_accordion(),
            _model_action_panel(),
            _protein_stl_panel(),
            _materialization_support_panel(),
        ),
        rx.cond(
            ComposeState.generating,
            rx.el.div(
                rx.el.div(
                    fomantic_icon("cog", size=28, style={"animation": "me-spin 2s linear infinite", "color": "#7c3aed"}),
                    style={"textAlign": "center", "marginBottom": "16px"},
                ),
                rx.el.p(
                    "Growing your printable crystal…",
                    style={"color": "#e0d6f7", "fontSize": "1.05rem", "textAlign": "center", "marginBottom": "12px", "fontWeight": "500"},
                ),
                rx.el.div(
                    rx.el.div(
                        style={
                            "height": "100%",
                            "width": "40%",
                            "borderRadius": "6px",
                            "background": "linear-gradient(90deg, #7c3aed, #a78bfa, #7c3aed)",
                            "backgroundSize": "200% 100%",
                            "animation": "me-progress-slide 1.8s ease-in-out infinite",
                        },
                    ),
                    style={
                        "width": "280px",
                        "height": "6px",
                        "borderRadius": "6px",
                        "backgroundColor": "rgba(124, 58, 237, 0.15)",
                        "margin": "0 auto",
                        "overflow": "hidden",
                    },
                ),
                rx.el.p(
                    "The viewer will appear here as soon as it is ready.",
                    style={"color": "#9ca3af", "fontSize": "0.82rem", "textAlign": "center", "marginTop": "10px"},
                ),
                rx.el.style(
                    "@keyframes me-progress-slide { 0% { transform: translateX(-100%); } 100% { transform: translateX(350%); } }"
                ),
                style={"padding": "40px 12px"},
            ),
            rx.el.p(
                "Click Materialize from Character profile to grow your printable crystal.",
                style={"color": "#9ca3af", "fontSize": "0.9rem", "textAlign": "center", "padding": "24px 12px"},
            ),
        ),
    )


def _sculpture_section() -> rx.Component:
    """Collapsible printable model section, with the viewer first."""
    body = rx.cond(
        ComposeState.viewer_expanded,
        _sculpture_section_body(),
        rx.fragment(),
    )

    return rx.el.div(
        _section_header(
            expanded=ComposeState.viewer_expanded,
            icon_name="cube",
            title="Printable crystal",
            on_toggle=ComposeState.toggle_viewer_expanded,
            right_badge=rx.cond(
                ComposeState.generating,
                rx.el.div(
                    fomantic_icon("sync", size=12, style={"animation": "me-spin 1s linear infinite"}),
                    rx.el.span(" Generating\u2026", style={"marginLeft": "4px", "fontSize": "0.75rem", "color": "#7c3aed"}),
                    style={"display": "flex", "alignItems": "center"},
                ),
                rx.cond(
                    ComposeState.has_stl,
                    rx.el.span("Ready", class_name="ui mini green label"),
                    rx.fragment(),
                ),
            ),
        ),
        body,
        style=_COLLAPSIBLE_STYLE,
    )


# ── Share & Report ───────────────────────────────────────────────────────────


_REPORT_CARD_STYLE: dict = {
    "background": "linear-gradient(180deg, #111827 0%, #0b1020 100%)",
    "border": "1px solid rgba(124, 58, 237, 0.48)",
    "borderRadius": "14px",
    "padding": "24px",
    "marginBottom": "16px",
    "position": "relative",
    "overflow": "hidden",
    "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
    "boxShadow": "0 18px 45px rgba(15, 23, 42, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.04)",
    "color": "#e5e7eb",
}


_VIEW_TILE_STYLE: dict = {
    "flex": "1 1 0",
    "aspectRatio": "1 / 1",
    "background": "radial-gradient(circle at 50% 38%, rgba(56, 189, 248, 0.14), rgba(11, 11, 20, 0.98) 64%)",
    "border": "1px solid rgba(124, 58, 237, 0.72)",
    "borderRadius": "10px",
    "display": "flex",
    "flexDirection": "column",
    "alignItems": "center",
    "justifyContent": "center",
    "position": "relative",
    "overflow": "hidden",
    "boxShadow": "0 0 18px rgba(124, 58, 237, 0.18)",
}


_SOCIAL_BUTTON_STYLE: dict = {
    "flex": "1 1 0",
    "height": "48px",
    "fontSize": "0.95rem",
    "fontWeight": "600",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "gap": "8px",
    "padding": "0 16px",
}

_TRANSPARENT_PX = (
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def _report_gene_row(gene_item: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                gene_item["gene"],
                style={
                    "fontWeight": "900",
                    "color": "#f8fafc",
                    "marginRight": "10px",
                    "minWidth": "80px",
                    "display": "inline-block",
                },
            ),
            _confidence_signal_bars(gene_item["confidence_primary"]["value"]),
            rx.el.span(
                gene_item["category_detail"],
                style={
                    "fontSize": "0.88rem",
                    "color": _gene_category_accent_color(gene_item["category"]),
                    "fontWeight": "600",
                },
            ),
            style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"},
        ),
        rx.el.div(
            _gene_confidence_section(
                gene_item["confidence_primary"],
                gene_item["confidence_details"],
                show_details=True,
            ),
            _gene_tested_on_row(gene_item["testing_entries"]),
            _gene_testing_table(gene_item["testing_entries"]),
            rx.cond(
                gene_item["evidence_tier"] != "",
                rx.el.div(
                    rx.el.span(
                        "Evidence tier",
                        style={
                            "fontSize": "0.8rem",
                            "fontWeight": "800",
                            "color": "#94a3b8",
                            "marginRight": "8px",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.06em",
                        },
                    ),
                    rx.el.span(
                        gene_item["evidence_tier"],
                        style={"fontSize": "0.88rem", "color": "#cbd5e1", "lineHeight": "1.45"},
                    ),
                    style={"display": "flex", "alignItems": "baseline", "flexWrap": "wrap", "gap": "4px"},
                ),
                rx.fragment(),
            ),
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "4px",
                "marginTop": "4px",
            },
        ),
        rx.el.p(
            gene_item["short_description"],
            class_name="me-report-desc",
            style={"fontSize": "0.86rem", "color": "#dbeafe", "margin": "2px 0 0 0", "lineHeight": "1.5"},
        ),
        style={
            "padding": "8px 12px",
            "borderRadius": "8px",
            "borderTop": "1px solid rgba(148, 163, 184, 0.22)",
            "borderRight": "1px solid rgba(148, 163, 184, 0.22)",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.22)",
            "borderLeft": _gene_category_border_left(gene_item["category"]),
            "background": "linear-gradient(135deg, rgba(30, 41, 59, 0.86), rgba(30, 27, 75, 0.68))",
            "marginBottom": "8px",
            "boxShadow": "0 0 18px rgba(124, 58, 237, 0.10)",
        },
    )


def _species_name_link(
    common_name: rx.Var,
    scientific_name: rx.Var,
    species_url: rx.Var,
    *,
    sci_style: dict | None = None,
) -> rx.Component:
    """Species name that links to Wikipedia when a URL is available."""
    default_sci_style = {"fontStyle": "italic", "color": "#94a3b8", "fontWeight": "400"}
    if sci_style:
        default_sci_style.update(sci_style)
    name_content = rx.fragment(
        rx.el.span(common_name, style={"fontWeight": "900", "color": "#f8fafc"}),
        " ",
        rx.el.span(scientific_name, style=default_sci_style),
    )
    return rx.cond(
        species_url != "",
        rx.el.a(
            name_content,
            href=species_url,
            target="_blank",
            rel="noopener noreferrer",
            style={"textDecoration": "none", "color": "inherit", "_hover": {"textDecoration": "underline", "textDecorationColor": "#94a3b8"}},
        ),
        rx.el.span(name_content),
    )


def _report_animal_row(animal_item: rx.Var) -> rx.Component:
    """Puzzle glyph + species name + traits; parent uses two columns."""
    text_block = rx.el.div(
        rx.el.div(
            _species_name_link(animal_item["common_name"], animal_item["scientific_name"], animal_item["species_url"]),
            style={"fontSize": "0.85rem", "lineHeight": "1.3"},
        ),
        rx.el.div(
            rx.el.span("Traits: ", style={"color": "#94a3b8", "fontWeight": "800", "fontSize": "0.72rem"}),
            rx.el.span(
                animal_item["traits_csv"],
                style={"color": "#cbd5e1", "fontSize": "0.78rem", "lineHeight": "1.4"},
            ),
        ),
        style={"overflow": "hidden"},
    )
    return rx.cond(
        animal_item["puzzle_src"] != "",
        rx.el.div(
            rx.el.img(
                src=animal_item["puzzle_src"],
                alt="",
                style={
                    "float": "left",
                    "maxWidth": "58px",
                    "maxHeight": "72px",
                    "width": "auto",
                    "height": "auto",
                    "objectFit": "contain",
                    "display": "block",
                    "marginRight": "8px",
                    "marginBottom": "2px",
                    "filter": "brightness(0) invert(1)",
                },
            ),
            text_block,
            style={
                "overflow": "hidden",
                "padding": "6px 0",
                "borderBottom": "1px solid rgba(148, 163, 184, 0.18)",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
        rx.el.div(
            rx.el.div(
                fomantic_icon("paw", size=12, color="#16a085", style={"marginRight": "6px", "verticalAlign": "middle"}),
                _species_name_link(
                    animal_item["common_name"],
                    animal_item["scientific_name"],
                    animal_item["species_url"],
                    sci_style={"fontSize": "0.78rem"},
                ),
                style={"display": "block", "lineHeight": "1.4", "marginBottom": "2px"},
            ),
            rx.el.div(
                animal_item["traits_csv"],
                style={"fontSize": "0.86rem", "color": "#cbd5e1", "lineHeight": "1.5", "paddingLeft": "18px"},
            ),
            style={
                "padding": "8px 0",
                "borderBottom": "1px solid rgba(148, 163, 184, 0.18)",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
    )


def _report_category_chip(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        cat_item,
        style={
            "display": "inline-block",
            "padding": "4px 10px",
            "borderRadius": "12px",
            "backgroundColor": "rgba(124, 58, 237, 0.18)",
            "color": "#c4b5fd",
            "fontSize": "0.82rem",
            "fontWeight": "800",
            "margin": "3px",
            "border": "1px solid rgba(167, 139, 250, 0.42)",
        },
    )


def _report_view_tile(label: str, img_id: str) -> rx.Component:
    return rx.el.div(
        rx.el.img(
            id=img_id,
            src=_TRANSPARENT_PX,
            alt="",
            style={"width": "100%", "height": "100%", "objectFit": "contain", "display": "block"},
        ),
        rx.el.div(
            label,
            style={
                "position": "absolute",
                "bottom": "6px",
                "left": "8px",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.72rem",
                "fontWeight": "900",
                "letterSpacing": "0.15em",
                "color": "#ddd6fe",
                "textShadow": "0 1px 2px rgba(0,0,0,0.7)",
            },
        ),
        style=_VIEW_TILE_STYLE,
    )


def _report_portrait(size_px: int = 84) -> rx.Component:
    return rx.cond(
        ComposeState.has_report_portrait,
        rx.el.img(
            src=ComposeState.report_portrait_data_url,
            alt="Uploaded report portrait",
            style={
                "width": f"{size_px}px",
                "height": f"{size_px}px",
                "objectFit": "cover",
                "borderRadius": "999px",
                "border": "2px solid rgba(167, 139, 250, 0.62)",
                "boxShadow": "0 0 22px rgba(124, 58, 237, 0.28)",
                "backgroundColor": "rgba(15, 23, 42, 0.72)",
                "flexShrink": "0",
            },
        ),
        rx.fragment(),
    )


def _report_character_note_block(font_size: str = "0.86rem") -> rx.Component:
    return rx.cond(
        ComposeState.has_report_character_note,
        rx.el.div(
            rx.el.div(
                "CHARACTER NOTE",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "4px",
                },
            ),
            rx.el.p(
                ComposeState.report_character_note,
                style={
                    "fontSize": font_size,
                    "color": "#dbeafe",
                    "lineHeight": "1.45",
                    "margin": "0",
                    "fontStyle": "italic",
                },
            ),
            style={
                "padding": "9px 11px",
                "border": "1px solid rgba(167, 139, 250, 0.28)",
                "borderRadius": "8px",
                "backgroundColor": "rgba(124, 58, 237, 0.12)",
                "marginBottom": "14px",
            },
        ),
        rx.fragment(),
    )


def _report_card() -> rx.Component:
    """The rasterizable RPG loadout report card used for on-screen sharing."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "LOADOUT #",
                style={"fontSize": "0.74rem", "fontWeight": "800"},
            ),
            rx.el.span(
                ComposeState.param_seed,
                style={"fontSize": "1.05rem", "fontWeight": "950"},
            ),
            style={
                "position": "absolute",
                "top": "18px",
                "right": "18px",
                "padding": "6px 12px",
                "border": "1px solid rgba(167, 139, 250, 0.52)",
                "borderRadius": "10px",
                "color": "#c4b5fd",
                "background": "rgba(15, 23, 42, 0.82)",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "letterSpacing": "0.1em",
                "boxShadow": "0 0 18px rgba(124, 58, 237, 0.24)",
                "pointerEvents": "none",
                "userSelect": "none",
            },
        ),
        rx.el.div(
            rx.el.div(
                "MATERIALIZED ENHANCEMENTS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.78rem",
                    "letterSpacing": "0.18em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                },
            ),
            rx.el.h2(
                "Character enhancement report",
                style={
                    "fontSize": "1.6rem",
                    "fontWeight": "950",
                    "color": "#f8fafc",
                    "margin": "2px 0 0 0",
                    "letterSpacing": "0.02em",
                },
            ),
            rx.el.p(
                "A shareable loadout generated from your selected enhancement genes.",
                style={
                    "fontSize": "0.94rem",
                    "fontWeight": "700",
                    "color": "#c4b5fd",
                    "margin": "4px 0 0 0",
                    "lineHeight": "1.35",
                },
            ),
            style={
                "borderBottom": "1px solid rgba(167, 139, 250, 0.36)",
                "paddingBottom": "12px",
                "paddingRight": "150px",
                "marginBottom": "14px",
            },
        ),
        rx.el.div(
            _report_portrait(86),
            rx.el.div(
                rx.el.span("CHARACTER", style={"fontSize": "0.78rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.4rem", "fontWeight": "900", "color": "#f8fafc"},
                ),
                style={"flex": "2 1 200px", "minWidth": "160px"},
            ),
            rx.el.div(
                rx.el.span("SEED", style={"fontSize": "0.78rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.2rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "1 1 80px", "minWidth": "80px"},
            ),
            rx.el.div(
                rx.el.span("POINTS", style={"fontSize": "0.78rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.2rem",
                        "fontWeight": "900",
                        "color": "#f8fafc",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "1 1 70px", "minWidth": "70px"},
            ),
            style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "14px"},
        ),
        _report_character_note_block(),
        rx.el.div(
            _report_view_tile("FRONT", "report-view-front"),
            _report_view_tile("SIDE", "report-view-side"),
            _report_view_tile("BACK", "report-view-back"),
            style={"display": "flex", "gap": "10px", "marginBottom": "16px"},
        ),
        rx.cond(
            ComposeState.report_views_ready,
            rx.fragment(),
            rx.el.p(
                "Generating three-view renders\u2026",
                style={
                    "textAlign": "center",
                    "fontSize": "0.82rem",
                    "color": "#94a3b8",
                    "margin": "-10px 0 12px 0",
                    "fontStyle": "italic",
                },
            ),
        ),
        rx.el.div(
            rx.el.div(
                "ENHANCEMENT CATEGORIES",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_categories, _report_category_chip),
                style={"display": "flex", "flexWrap": "wrap", "gap": "2px"},
            ),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                "SOURCE ORGANISMS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_animals, _report_animal_row),
                style={
                    "columnCount": 2,
                    "columnGap": "22px",
                    "columnFill": "balance",
                },
            ),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                "GENES IN COMPOSITION",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.85rem",
                    "letterSpacing": "0.12em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(_foreach_included_catalog_gene(_report_gene_row)),
            style={"marginBottom": "14px"},
        ),
        rx.el.div(
            rx.el.div(
                "enhancement.bio",
                style={"fontSize": "0.9rem", "fontWeight": "900", "color": "#c4b5fd"},
            ),
            style={
                "paddingTop": "12px",
                "borderTop": "1px solid rgba(167, 139, 250, 0.28)",
            },
        ),
        id="me-report-card",
        style=_REPORT_CARD_STYLE,
    )


def _png_animal_row(animal_item: rx.Var) -> rx.Component:
    """Square PNG: three columns; bounded text wraps vertically; one primary trait."""
    text_block = rx.el.div(
        rx.el.div(
            rx.el.span(animal_item["common_name"], style={"fontWeight": "900", "color": "#f8fafc"}),
            style={
                "fontSize": "0.58rem",
                "lineHeight": "1.15",
                "marginBottom": "2px",
                "maxWidth": "100%",
                "overflowWrap": "anywhere",
                "wordBreak": "break-word",
            },
        ),
        rx.el.div(
            rx.el.span("Trait: ", style={"color": "#94a3b8", "fontWeight": "800", "fontSize": "0.5rem"}),
            rx.el.span(
                animal_item["primary_trait"],
                style={
                    "color": "#cbd5e1",
                    "fontSize": "0.5rem",
                    "lineHeight": "1.15",
                    "overflowWrap": "anywhere",
                    "wordBreak": "break-word",
                },
            ),
            style={"maxWidth": "100%", "maxHeight": "3.6em", "overflow": "hidden"},
        ),
        style={
            "overflow": "hidden",
            "maxWidth": "100%",
            "display": "block",
        },
    )
    return rx.cond(
        animal_item["puzzle_src"] != "",
        rx.el.div(
            rx.el.img(
                src=animal_item["puzzle_src"],
                alt="",
                style={
                    "float": "left",
                    "display": "block",
                    "maxWidth": "34px",
                    "maxHeight": "46px",
                    "width": "auto",
                    "height": "auto",
                    "objectFit": "contain",
                    "marginRight": "4px",
                    "marginBottom": "2px",
                    "filter": "brightness(0) invert(1)",
                },
            ),
            text_block,
            style={
                "overflow": "hidden",
                "width": "100%",
                "boxSizing": "border-box",
                "clear": "both",
                "paddingBottom": "4px",
                "marginBottom": "3px",
                "borderBottom": "1px solid rgba(148, 163, 184, 0.18)",
                "breakInside": "avoid",
                "WebkitColumnBreakInside": "avoid",
                "pageBreakInside": "avoid",
            },
        ),
        rx.el.div(
            rx.el.span("\u2022 ", style={"color": "#16a085", "fontWeight": "700"}),
            rx.el.span(animal_item["common_name"], style={"fontWeight": "900", "color": "#f8fafc"}),
            rx.el.span(" \u2014 ", style={"color": "#94a3b8"}),
            rx.el.span(animal_item["primary_trait"], style={"color": "#cbd5e1", "fontSize": "0.6rem"}),
            style={
                "fontSize": "0.65rem",
                "lineHeight": "1.35",
                "padding": "3px 0",
                "display": "block",
                "clear": "both",
                "maxWidth": "100%",
                "overflowWrap": "anywhere",
            },
        ),
    )


def _png_category_chip(cat_item: rx.Var) -> rx.Component:
    return rx.el.span(
        cat_item,
        style={
            "display": "inline-block",
            "padding": "5px 12px",
            "borderRadius": "14px",
            "backgroundColor": "rgba(124, 58, 237, 0.18)",
            "color": "#c4b5fd",
            "fontSize": "0.78rem",
            "fontWeight": "800",
            "margin": "3px",
            "border": "1px solid rgba(167, 139, 250, 0.42)",
        },
    )


def _png_gene_row(gene_item: rx.Var) -> rx.Component:
    """One compact line per gene for the 1080\u00d71080 PNG card (matches on-card section)."""
    return rx.el.div(
        rx.el.span(
            gene_item["gene"],
            style={
                "fontWeight": "900",
                "color": "#f8fafc",
                "fontSize": "0.56rem",
                "marginRight": "4px",
            },
        ),
        rx.el.span("\u2014 ", style={"color": "#94a3b8", "fontSize": "0.52rem"}),
        rx.el.span(
            gene_item["category_detail"],
            style={
                "fontSize": "0.54rem",
                "color": _gene_category_accent_color(gene_item["category"]),
                "fontWeight": "600",
            },
        ),
        rx.el.span(" (", style={"color": "#94a3b8", "fontSize": "0.52rem"}),
        rx.el.span(
            gene_item["species_common_names"],
            style={"color": "#5eead4", "fontWeight": "800", "fontSize": "0.52rem"},
        ),
        rx.el.span(")", style={"color": "#94a3b8", "fontSize": "0.52rem"}),
        style={
            "lineHeight": "1.2",
            "padding": "3px 0",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.18)",
            "breakInside": "avoid",
            "WebkitColumnBreakInside": "avoid",
        },
    )


def _png_view_tile(label: str, img_id: str) -> rx.Component:
    """One sculpture panel; parent row sets fixed height (no 1:1 aspect) so the 1080\u00d71080 card fits."""
    return rx.el.div(
        rx.el.img(
            id=img_id,
            src=_TRANSPARENT_PX,
            alt="",
            style={"width": "100%", "height": "100%", "objectFit": "contain", "display": "block"},
        ),
        rx.el.div(
            label,
            style={
                "position": "absolute",
                "bottom": "6px",
                "left": "8px",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.65rem",
                "fontWeight": "700",
                "letterSpacing": "0.16em",
                "color": "#c4b5fd",
                "textShadow": "0 1px 2px rgba(0,0,0,0.8)",
            },
        ),
        style={
            "flex": "1 1 0",
            "minWidth": "0",
            "minHeight": "0",
            "height": "100%",
            "background": "radial-gradient(circle at 50% 38%, rgba(56, 189, 248, 0.14), rgba(11, 11, 20, 0.98) 64%)",
            "border": "1px solid rgba(124, 58, 237, 0.72)",
            "borderRadius": "10px",
            "position": "relative",
            "overflow": "hidden",
            "boxShadow": "0 0 18px rgba(124, 58, 237, 0.18)",
        },
    )


def _report_png_card() -> rx.Component:
    """Dedicated 1080x1080 card — this is the element rasterized into the social PNG.

    Flex column: scrollable middle (views fixed height, organisms flex-shrink) keeps the
    brand footer inside the frame. Dense layouts clip organisms/genes before the footer.
    """
    main_column = rx.el.div(
        # Header
        rx.el.div(
            rx.el.div(
                "MATERIALIZED ENHANCEMENTS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.82rem",
                    "letterSpacing": "0.2em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                },
            ),
            rx.el.h2(
                "Character enhancement report",
                style={
                    "fontSize": "2rem",
                    "fontWeight": "950",
                    "color": "#f8fafc",
                    "margin": "4px 0 0 0",
                    "letterSpacing": "0.02em",
                },
            ),
            style={
                "borderBottom": "1px solid rgba(167, 139, 250, 0.36)",
                "paddingBottom": "12px",
                "marginBottom": "18px",
            },
        ),
        # NAME / SEED / POINTS row
        rx.el.div(
            _report_portrait(96),
            rx.el.div(
                rx.el.div("CHARACTER", style={"fontSize": "0.82rem", "color": "#94a3b8", "letterSpacing": "0.14em", "marginBottom": "2px", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.input_personal_tag,
                    style={"fontSize": "1.55rem", "fontWeight": "900", "color": "#f8fafc"},
                ),
                style={"flex": "2 1 300px", "minWidth": "200px"},
            ),
            rx.el.div(
                rx.el.div("SEED", style={"fontSize": "0.82rem", "color": "#94a3b8", "letterSpacing": "0.14em", "marginBottom": "2px", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.param_seed,
                    style={
                        "fontSize": "1.4rem",
                        "fontWeight": "700",
                        "color": "#7c3aed",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "0 0 110px"},
            ),
            rx.el.div(
                rx.el.div("POINTS", style={"fontSize": "0.82rem", "color": "#94a3b8", "letterSpacing": "0.14em", "marginBottom": "2px", "fontWeight": "800"}),
                rx.el.div(
                    ComposeState.param_points,
                    style={
                        "fontSize": "1.4rem",
                        "fontWeight": "900",
                        "color": "#f8fafc",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    },
                ),
                style={"flex": "0 0 90px"},
            ),
            style={"display": "flex", "gap": "20px", "marginBottom": "16px"},
        ),
        _report_character_note_block("0.78rem"),
        # Categories on top
        rx.el.div(
            rx.el.div(
                "ENHANCEMENT CATEGORIES",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_categories, _png_category_chip),
                style={"display": "flex", "flexWrap": "wrap", "gap": "2px"},
            ),
            style={"marginBottom": "18px"},
        ),
        # Three views — fixed row height so square card can fit footer + genes + organisms
        rx.el.div(
            _png_view_tile("FRONT", "png-view-front"),
            _png_view_tile("SIDE", "png-view-side"),
            _png_view_tile("BACK", "png-view-back"),
            style={
                "display": "flex",
                "gap": "10px",
                "height": "200px",
                "marginBottom": "12px",
                "flexShrink": "0",
            },
        ),
        # Animals: flex fills slack; inner columns clip if the report is very dense
        rx.el.div(
            rx.el.div(
                "SOURCE ORGANISMS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                    "flexShrink": "0",
                },
            ),
            rx.el.div(
                rx.foreach(ComposeState.selected_animals, _png_animal_row),
                style={
                    "columnCount": 3,
                    "columnGap": "12px",
                    "columnFill": "balance",
                    "flex": "1 1 auto",
                    "minHeight": "0",
                    "overflow": "hidden",
                },
            ),
            style={
                "display": "flex",
                "flexDirection": "column",
                "flex": "1 1 0",
                "minHeight": "0",
                "overflow": "hidden",
                "marginBottom": "8px",
            },
        ),
        rx.el.div(
            rx.el.div(
                "GENES IN COMPOSITION",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.72rem",
                    "letterSpacing": "0.14em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                    "marginBottom": "6px",
                    "flexShrink": "0",
                },
            ),
            rx.el.div(
                _foreach_included_catalog_gene(_png_gene_row),
                style={
                    "columnCount": "2",
                    "columnGap": "12px",
                    "columnFill": "balance",
                    "flex": "0 1 auto",
                    "minHeight": "0",
                    "maxHeight": "168px",
                    "overflow": "hidden",
                },
            ),
            style={"flexShrink": "0", "marginBottom": "4px"},
        ),
        style={
            "display": "flex",
            "flexDirection": "column",
            "flex": "1 1 auto",
            "minHeight": "0",
            "overflow": "hidden",
        },
    )
    footer = rx.el.div(
        rx.el.div(
            "enhancement.bio",
            style={"fontSize": "0.95rem", "fontWeight": "900", "color": "#c4b5fd"},
        ),
        style={
            "paddingTop": "10px",
            "paddingBottom": "6px",
            "borderTop": "1px solid rgba(167, 139, 250, 0.28)",
            "textAlign": "center",
            "flexShrink": "0",
        },
    )
    return rx.el.div(
        rx.el.div(
            rx.el.span("LOADOUT #", style={"fontSize": "0.9rem", "fontWeight": "800"}),
            rx.el.span(ComposeState.param_seed, style={"fontSize": "1.3rem", "fontWeight": "950"}),
            style={
                "position": "absolute",
                "top": "24px",
                "right": "24px",
                "padding": "6px 16px",
                "border": "1px solid rgba(167, 139, 250, 0.52)",
                "borderRadius": "10px",
                "color": "#c4b5fd",
                "background": "rgba(15, 23, 42, 0.82)",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "letterSpacing": "0.1em",
                "boxShadow": "0 0 18px rgba(124, 58, 237, 0.24)",
                "zIndex": "2",
            },
        ),
        main_column,
        footer,
        id="me-report-png-card",
        style={
            "position": "absolute",
            "left": "-12000px",
            "top": "0",
            "width": "1080px",
            "height": "1080px",
            "padding": "40px",
            "background": "linear-gradient(180deg, #111827 0%, #0b1020 100%)",
            "border": "2px solid rgba(124, 58, 237, 0.62)",
            "boxSizing": "border-box",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
            "color": "#e5e7eb",
        },
    )


def _char_body_marker(category: str, top: str, left: str) -> rx.Component:
    """Static body-map marker for the character card — colored dot with count badge."""
    color = CATEGORY_COLORS.get(category, "#7c3aed")
    count = ComposeState.active_display_gene_counts[category]
    return rx.cond(
        count > 0,
        rx.el.div(
            rx.el.div(
                style={
                    "width": "24px",
                    "height": "24px",
                    "borderRadius": "999px",
                    "background": f"radial-gradient(circle, {color}, {color}88)",
                    "border": f"2px solid {color}",
                    "boxShadow": f"0 0 14px {color}, 0 0 28px {color}55",
                },
            ),
            rx.el.div(
                count,
                style={
                    "position": "absolute",
                    "right": "-5px",
                    "top": "-5px",
                    "minWidth": "15px",
                    "height": "15px",
                    "padding": "0 3px",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "borderRadius": "999px",
                    "background": color,
                    "color": "#ffffff",
                    "fontSize": "0.5rem",
                    "fontWeight": "950",
                    "lineHeight": "1",
                },
            ),
            rx.el.div(
                category,
                style={
                    "position": "absolute",
                    "left": "50%",
                    "top": "100%",
                    "transform": "translateX(-50%)",
                    "marginTop": "2px",
                    "whiteSpace": "nowrap",
                    "fontSize": "0.5rem",
                    "fontWeight": "900",
                    "color": color,
                    "textShadow": "0 1px 6px rgba(0,0,0,0.9)",
                },
            ),
            style={
                "position": "absolute",
                "top": top,
                "left": left,
                "transform": "translate(-50%, -50%)",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        ),
        rx.fragment(),
    )


def _char_gene_row(gene_item: rx.Var) -> rx.Component:
    """Gene entry for character card: colored name on first line, short description below."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                gene_item["gene"],
                style={
                    "fontWeight": "900",
                    "color": _gene_category_accent_color(gene_item["category"]),
                    "fontSize": "0.6rem",
                },
            ),
            rx.el.span(
                " — ",
                style={"color": "#64748b", "fontSize": "0.54rem"},
            ),
            rx.el.span(
                gene_item["category_detail"],
                style={"color": "#94a3b8", "fontSize": "0.52rem", "fontWeight": "600"},
            ),
        ),
        rx.el.div(
            gene_item["short_description"],
            style={
                "color": "#cbd5e1",
                "fontSize": "0.5rem",
                "lineHeight": "1.2",
                "overflow": "hidden",
                "display": "-webkit-box",
                "WebkitLineClamp": "2",
                "WebkitBoxOrient": "vertical",
            },
        ),
        style={
            "padding": "3px 0",
            "borderBottom": "1px solid rgba(148, 163, 184, 0.12)",
            "breakInside": "avoid",
            "WebkitColumnBreakInside": "avoid",
        },
    )


def _report_png_card_character() -> rx.Component:
    """Character card 1080x1080 — body-map + front model view + nicely formatted gene list."""
    body_map = rx.el.div(
        rx.el.img(
            src="/images/body_only.webp",
            alt="Enhancement body map",
            style={
                "position": "absolute",
                "left": "50%",
                "top": "50%",
                "transform": "translate(-50%, -50%)",
                "height": "90%",
                "width": "auto",
                "objectFit": "contain",
                "opacity": "0.5",
                "filter": "brightness(1.4) contrast(0.9)",
            },
        ),
        _char_body_marker("Expression", "14%", "22%"),
        _char_body_marker("Perception", "14%", "78%"),
        _char_body_marker("Longevity & Genome", "48%", "22%"),
        _char_body_marker("Stress Resistance", "48%", "78%"),
        _char_body_marker("Environmental Adaptation", "78%", "22%"),
        _char_body_marker("Regeneration", "78%", "78%"),
        style={
            "position": "relative",
            "flex": "1 1 0",
            "minWidth": "0",
            "height": "100%",
            "background": "radial-gradient(ellipse at 50% 45%, rgba(124, 58, 237, 0.10), rgba(11, 11, 20, 0.96) 70%)",
            "border": "1px solid rgba(124, 58, 237, 0.32)",
            "borderRadius": "14px",
            "overflow": "hidden",
        },
    )
    model_view = rx.el.div(
        rx.el.img(
            id="char-view-front",
            src=_TRANSPARENT_PX,
            alt="3D model — front view",
            style={"width": "100%", "height": "100%", "objectFit": "contain", "display": "block"},
        ),
        rx.el.div(
            "FRONT",
            style={
                "position": "absolute",
                "bottom": "6px",
                "left": "8px",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.6rem",
                "fontWeight": "700",
                "letterSpacing": "0.16em",
                "color": "#c4b5fd",
                "textShadow": "0 1px 2px rgba(0,0,0,0.8)",
            },
        ),
        style={
            "flex": "1 1 0",
            "minWidth": "0",
            "height": "100%",
            "background": "radial-gradient(circle at 50% 38%, rgba(56, 189, 248, 0.14), rgba(11, 11, 20, 0.98) 64%)",
            "border": "1px solid rgba(124, 58, 237, 0.52)",
            "borderRadius": "14px",
            "position": "relative",
            "overflow": "hidden",
        },
    )
    top_visuals = rx.el.div(
        body_map,
        model_view,
        style={
            "display": "flex",
            "gap": "12px",
            "height": "380px",
            "flexShrink": "0",
            "marginBottom": "14px",
        },
    )
    info_row = rx.el.div(
        _report_portrait(72),
        rx.el.div(
            rx.el.div("CHARACTER", style={"fontSize": "0.72rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
            rx.el.div(ComposeState.input_personal_tag, style={"fontSize": "1.4rem", "fontWeight": "900", "color": "#f8fafc"}),
            style={"flex": "2 1 200px", "minWidth": "140px"},
        ),
        rx.el.div(
            rx.el.div("SEED", style={"fontSize": "0.72rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
            rx.el.div(ComposeState.param_seed, style={"fontSize": "1.2rem", "fontWeight": "700", "color": "#7c3aed", "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace"}),
            style={"flex": "0 0 80px"},
        ),
        rx.el.div(
            rx.el.div("POINTS", style={"fontSize": "0.72rem", "color": "#94a3b8", "letterSpacing": "0.12em", "fontWeight": "800"}),
            rx.el.div(ComposeState.param_points, style={"fontSize": "1.2rem", "fontWeight": "900", "color": "#f8fafc", "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace"}),
            style={"flex": "0 0 70px"},
        ),
        style={"display": "flex", "gap": "14px", "marginBottom": "8px"},
    )
    categories_row = rx.el.div(
        rx.foreach(ComposeState.selected_categories, _png_category_chip),
        style={"display": "flex", "flexWrap": "wrap", "gap": "3px", "marginBottom": "8px"},
    )
    gene_list = rx.el.div(
        rx.el.div(
            "ENHANCEMENT GENES",
            style={
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "fontSize": "0.62rem",
                "letterSpacing": "0.14em",
                "color": "#a78bfa",
                "fontWeight": "900",
                "marginBottom": "4px",
                "flexShrink": "0",
            },
        ),
        rx.el.div(
            _foreach_included_catalog_gene(_char_gene_row),
            style={
                "columnCount": "2",
                "columnGap": "16px",
                "columnFill": "balance",
                "flex": "1 1 auto",
                "minHeight": "0",
                "overflow": "hidden",
            },
        ),
        style={
            "display": "flex",
            "flexDirection": "column",
            "flex": "1 1 auto",
            "minHeight": "0",
            "overflow": "hidden",
        },
    )
    footer = rx.el.div(
        rx.el.div(
            "enhancement.bio",
            style={"fontSize": "0.9rem", "fontWeight": "900", "color": "#c4b5fd"},
        ),
        style={
            "paddingTop": "8px",
            "borderTop": "1px solid rgba(167, 139, 250, 0.28)",
            "textAlign": "center",
            "flexShrink": "0",
        },
    )
    return rx.el.div(
        rx.el.div(
            rx.el.span("LOADOUT #", style={"fontSize": "0.85rem", "fontWeight": "800"}),
            rx.el.span(ComposeState.param_seed, style={"fontSize": "1.2rem", "fontWeight": "950"}),
            style={
                "position": "absolute",
                "top": "20px",
                "right": "24px",
                "padding": "5px 14px",
                "border": "1px solid rgba(167, 139, 250, 0.52)",
                "borderRadius": "10px",
                "color": "#c4b5fd",
                "background": "rgba(15, 23, 42, 0.82)",
                "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                "letterSpacing": "0.1em",
                "boxShadow": "0 0 18px rgba(124, 58, 237, 0.24)",
                "zIndex": "2",
            },
        ),
        rx.el.div(
            rx.el.div(
                "MATERIALIZED ENHANCEMENTS",
                style={
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "fontSize": "0.78rem",
                    "letterSpacing": "0.2em",
                    "color": "#a78bfa",
                    "fontWeight": "900",
                },
            ),
            rx.el.div(
                "Character profile",
                style={
                    "fontSize": "1.5rem",
                    "fontWeight": "950",
                    "color": "#f8fafc",
                    "margin": "2px 0 0 0",
                },
            ),
            style={
                "borderBottom": "1px solid rgba(167, 139, 250, 0.36)",
                "paddingBottom": "8px",
                "paddingRight": "140px",
                "marginBottom": "10px",
            },
        ),
        top_visuals,
        info_row,
        categories_row,
        _report_character_note_block("0.72rem"),
        gene_list,
        footer,
        id="me-report-png-card-character",
        style={
            "position": "absolute",
            "left": "-12000px",
            "top": "0",
            "width": "1080px",
            "height": "1080px",
            "padding": "32px 36px",
            "background": "linear-gradient(180deg, #111827 0%, #0b1020 100%)",
            "border": "2px solid rgba(124, 58, 237, 0.62)",
            "boxSizing": "border-box",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
            "color": "#e5e7eb",
        },
    )


def _report_pdf_long_content() -> rx.Component:
    """Hidden DOM subtree rasterized as additional A4 PDF page(s)."""
    return rx.el.div(
        rx.el.h2(
            "Gene library \u2014 full descriptions",
            style={"fontSize": "1.3rem", "fontWeight": "700", "color": "#1a1a2e", "marginBottom": "8px"},
        ),
        rx.el.p(
            "The 3D model you just generated was shaped by the following genes. Each entry "
            "is a short narrative about the gene in its source organism (mechanistic detail is "
            "available in the Gene Library tab).",
            style={"fontSize": "0.82rem", "color": "#374151", "lineHeight": "1.6", "marginBottom": "10px"},
        ),
        _foreach_included_catalog_gene(
            lambda g: rx.el.div(
                rx.el.div(
                    rx.cond(
                        g["gene_url"] != "",
                        rx.el.a(
                            g["gene"],
                            href=g["gene_url"],
                            target="_blank",
                            rel="noopener noreferrer",
                            style={
                                "fontWeight": "700",
                                "color": "#1a1a2e",
                                "textDecoration": "none",
                                "borderBottom": "1px dotted #7c3aed",
                                "_hover": {"color": "#7c3aed"},
                            },
                        ),
                        rx.el.span(
                            g["gene"],
                            style={
                                "fontWeight": "700",
                                "color": "#1a1a2e",
                            },
                        ),
                    ),
                    rx.el.span(" \u2014 ", style={"color": "#9ca3af"}),
                    rx.el.span(
                        g["category_detail"],
                        style={"color": _gene_category_accent_color(g["category"]), "fontWeight": "600"},
                    ),
                    rx.el.span("  (", style={"color": "#9ca3af"}),
                    rx.cond(
                        g["species_page_url"] != "",
                        rx.el.a(
                            rx.el.span(g["species_common_names"], style={"fontWeight": "600"}),
                            " ",
                            rx.el.span(g["species_scientific_names"], style={"fontStyle": "italic"}),
                            href=g["species_page_url"],
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"color": "#0d9488", "textDecoration": "none", "_hover": {"textDecoration": "underline"}},
                        ),
                        rx.el.span(
                            rx.el.span(g["species_common_names"], style={"fontWeight": "600"}),
                            " ",
                            rx.el.span(g["species_scientific_names"], style={"fontStyle": "italic"}),
                            style={"color": "#0d9488"},
                        ),
                    ),
                    rx.el.span(")", style={"color": "#9ca3af"}),
                    style={"fontSize": "0.95rem", "marginBottom": "2px"},
                    data_gene=g["gene"],
                    data_trait=g["category_detail"],
                    data_organism=g["species_common_names"],
                    data_puzzle_src=g["puzzle_src"],
                ),
                rx.cond(
                    g["evidence_tier"] != "",
                    rx.el.p(
                        rx.el.span("Evidence tier: ", style={"color": "#9ca3af", "fontWeight": "600"}),
                        rx.el.span(g["evidence_tier"], style={"color": "#374151"}),
                        class_name="me-report-evidence-tier",
                        style={"fontSize": "0.74rem", "margin": "0 0 2px 0", "lineHeight": "1.45"},
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    g["confidence_entries"].length() > 0,
                    rx.el.div(
                        rx.el.span("Confidence: ", style={"color": "#9ca3af", "fontWeight": "600", "fontSize": "0.74rem"}),
                        rx.foreach(
                            g["confidence_entries"],
                            lambda ce: rx.el.span(
                                rx.el.span(ce["value"], style={
                                    "fontWeight": "600",
                                    "color": rx.match(
                                        ce["value"].lower(),
                                        ("very high", "#047857"),
                                        ("high", "#047857"),
                                        ("medium-high", "#0e7490"),
                                        ("medium", "#b45309"),
                                        ("medium-low", "#b91c1c"),
                                        ("low-medium", "#b91c1c"),
                                        ("low", "#b91c1c"),
                                        ("declining", "#b91c1c"),
                                        "#4b5563",
                                    ),
                                }),
                                rx.cond(
                                    ce["argument"] != "",
                                    rx.el.span(
                                        " (",
                                        ce["argument"],
                                        ")",
                                        style={"color": "#374151"},
                                    ),
                                    rx.fragment(),
                                ),
                                rx.el.span("; ", style={"color": "#9ca3af"}),
                                style={"fontSize": "0.74rem"},
                            ),
                        ),
                        class_name="me-report-confidence",
                        style={"fontSize": "0.74rem", "margin": "0 0 2px 0", "lineHeight": "1.45", "display": "flex", "flexWrap": "wrap", "alignItems": "baseline"},
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    g["testing_entries"].length() > 0,
                    rx.el.div(
                        rx.el.span("Tested on: ", style={"color": "#9ca3af", "fontWeight": "600", "fontSize": "0.74rem"}),
                        rx.foreach(g["testing_entries"], lambda te: rx.el.span(
                            te["host"],
                            rx.cond(
                                te["tissue_or_system"] != "",
                                rx.el.span(
                                    " (", te["tissue_or_system"], ")",
                                    style={"color": "#9ca3af", "fontSize": "0.62rem"},
                                ),
                                rx.fragment(),
                            ),
                            style={
                                "display": "inline-flex",
                                "alignItems": "center",
                                "fontSize": "0.7rem",
                                "color": "#374151",
                                "background": "#f3f4f6",
                                "borderRadius": "3px",
                                "padding": "0 4px",
                                "marginRight": "3px",
                            },
                        )),
                        class_name="me-report-tested",
                        style={"display": "flex", "alignItems": "center", "gap": "2px", "flexWrap": "wrap", "margin": "0 0 4px 0"},
                    ),
                    rx.fragment(),
                ),
                rx.el.p(
                    g["description"],
                    class_name="me-report-desc",
                    style={"fontSize": "0.78rem", "color": "#374151", "margin": "0", "lineHeight": "1.55"},
                ),
                style={
                    "padding": "8px 12px",
                    "borderRadius": "4px",
                    "borderTop": "1px solid #e5e7eb",
                    "borderRight": "1px solid #e5e7eb",
                    "borderBottom": "1px solid #e5e7eb",
                    "borderLeft": _gene_category_border_left(g["category"]),
                    "backgroundColor": "#ffffff",
                    "marginBottom": "8px",
                },
            ),
        ),
        id="me-report-pdf-long",
        style={
            "position": "absolute",
            "left": "-10000px",
            "top": "0",
            "width": "180mm",
            "padding": "0",
            "backgroundColor": "#ffffff",
            "color": "#1a1a2e",
            "fontFamily": "'Lato', 'Helvetica Neue', Arial, sans-serif",
        },
    )


def _report_capture_iframe() -> rx.Component:
    """Always-mounted off-screen iframe rendering the 3 booking-photo views."""
    return rx.el.iframe(
        src=rx.cond(
            ComposeState.has_stl,
            ComposeState.capture_iframe_src,
            "about:blank",
        ),
        id="sculpture-capture-iframe",
        style={
            "position": "fixed",
            "left": "-10000px",
            "top": "0",
            "width": "720px",
            "height": "720px",
            "border": "0",
            "pointerEvents": "none",
            "visibility": "hidden",
        },
    )


def _published_report_link(label: str, href: rx.Var, icon_name: str) -> rx.Component:
    return rx.el.a(
        fomantic_icon(icon_name, size=14),
        rx.el.span(label, style={"marginLeft": "6px"}),
        href=href,
        target="_blank",
        rel="noopener noreferrer",
        class_name="ui button",
        style={**_SOCIAL_BUTTON_STYLE, "fontSize": "0.82rem"},
    )


def _published_report_links() -> rx.Component:
    return rx.cond(
        ComposeState.has_published_report,
        rx.el.div(
            rx.el.div(
                "Generated public report",
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "700",
                    "color": "#cbd5e1",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                    "marginBottom": "8px",
                },
            ),
            rx.el.div(
                _published_report_link("Open PDF", ComposeState.report_pdf_url, "file pdf outline"),
                _published_report_link("Open public report", ComposeState.report_public_url, "external alternate"),
                _published_report_link("STL model", ComposeState.report_model_url, "cube"),
                _published_report_link("Params", ComposeState.report_params_url, "code"),
                style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
            ),
            rx.el.div(
                ComposeState.report_public_url,
                style={
                    "fontSize": "0.76rem",
                    "color": "#9ca3af",
                    "marginTop": "8px",
                    "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                    "wordBreak": "break-all",
                },
            ),
            style={
                "marginTop": "10px",
                "padding": "10px",
                "border": "1px solid rgba(148, 163, 184, 0.24)",
                "borderRadius": "8px",
                "backgroundColor": "rgba(15, 23, 42, 0.35)",
            },
        ),
        rx.fragment(),
    )


def _generate_public_link_button() -> rx.Component:
    return rx.el.button(
        fomantic_icon("cloud upload", size=16),
        rx.el.span(
            rx.cond(
                ComposeState.report_publishing,
                " Creating public link...",
                rx.cond(
                    ComposeState.has_published_report,
                    " Update public link",
                    " Create public link",
                ),
            ),
            style={"marginLeft": "2px"},
        ),
        on_click=ComposeState.start_report_publish,
        class_name=rx.cond(
            ComposeState.can_publish_report,
            "ui primary button",
            "ui disabled button",
        ),
        style={**_SOCIAL_BUTTON_STYLE, "flex": "0 1 auto", "minWidth": "220px"},
    )


def _report_hidden_capture_content() -> rx.Component:
    """Keep export-only report DOM mounted off-screen for JS PDF/PNG builders."""
    return rx.el.div(
        _report_card(),
        _report_png_card(),
        _report_png_card_character(),
        _report_pdf_long_content(),
        aria_hidden="true",
        style={
            "position": "fixed",
            "left": "-10000px",
            "top": "0",
            "width": "820px",
            "height": "1px",
            "overflow": "visible",
            "pointerEvents": "none",
            "opacity": "1",
        },
    )


def _report_portrait_upload_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Customize report",
            style={
                "width": "100%",
                "fontSize": "0.78rem",
                "fontWeight": "700",
                "color": "#cbd5e1",
                "textTransform": "uppercase",
                "letterSpacing": "0.08em",
            },
        ),
        rx.el.p(
            "Optional: choose a portrait or user picture. It is applied immediately to the report card, PNG, PDF, and public link.",
            style={"width": "100%", "margin": "0", "fontSize": "0.82rem", "color": "#9ca3af"},
        ),
        rx.el.label(
            "Character note",
            style={"fontSize": "0.82rem", "fontWeight": "700", "color": "#cbd5e1"},
        ),
        rx.el.textarea(
            value=ComposeState.report_character_note,
            on_change=ComposeState.set_report_character_note,
            placeholder="Optional: explain this profile, dedication, prompt, or story.",
            max_length=420,
            rows=3,
            style={
                "width": "min(100%, 420px)",
                "resize": "vertical",
                "border": "1px solid rgba(167, 139, 250, 0.42)",
                "borderRadius": "8px",
                "backgroundColor": "rgba(15, 23, 42, 0.72)",
                "color": "#e5e7eb",
                "padding": "9px 10px",
                "fontSize": "0.86rem",
                "lineHeight": "1.4",
            },
        ),
        rx.el.div(
            "Optional short note shown on the report. Editing it clears old share links so the public report can be updated.",
            style={"fontSize": "0.74rem", "color": "#9ca3af", "maxWidth": "420px"},
        ),
        rx.upload(
            rx.el.div(
                fomantic_icon("image outline", size=16),
                rx.el.span(" Drop image here or click to select", style={"marginLeft": "6px"}),
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "width": "100%",
                    "minHeight": "44px",
                    "color": "#cbd5e1",
                },
            ),
            id=_REPORT_PORTRAIT_UPLOAD_ID,
            on_drop=ComposeState.upload_report_portrait(
                rx.upload_files(upload_id=_REPORT_PORTRAIT_UPLOAD_ID)
            ),
            border="1px dashed rgba(167, 139, 250, 0.52)",
            border_radius="8px",
            padding="6px",
            width="min(100%, 420px)",
        ),
        rx.el.div(
            rx.foreach(rx.selected_files(_REPORT_PORTRAIT_UPLOAD_ID), lambda name: rx.el.span(name)),
            style={"fontSize": "0.76rem", "color": "#9ca3af", "wordBreak": "break-all"},
        ),
        rx.cond(
            ComposeState.has_report_portrait,
            rx.el.button(
                fomantic_icon("trash", size=14),
                rx.el.span(" Remove image", style={"marginLeft": "6px"}),
                on_click=ComposeState.clear_report_portrait,
                class_name="ui button",
                style={**_SOCIAL_BUTTON_STYLE, "fontSize": "0.82rem"},
            ),
            rx.fragment(),
        ),
        rx.cond(
            ComposeState.has_report_portrait,
            rx.el.div(
                _report_portrait(54),
                rx.el.span(
                    ComposeState.report_portrait_filename,
                    style={"fontSize": "0.78rem", "color": "#cbd5e1", "wordBreak": "break-all"},
                ),
                style={"display": "flex", "alignItems": "center", "gap": "10px"},
            ),
            rx.fragment(),
        ),
        rx.cond(
            ComposeState.report_portrait_error != "",
            _inline_notice(ComposeState.report_portrait_error),
            rx.fragment(),
        ),
        style={
            "display": "flex",
            "gap": "8px",
            "flexDirection": "column",
            "alignItems": "flex-start",
            "padding": "10px",
            "border": "1px solid rgba(148, 163, 184, 0.24)",
            "borderRadius": "8px",
            "backgroundColor": "rgba(15, 23, 42, 0.35)",
            "marginBottom": "10px",
        },
    )


def _report_pdf_viewer_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    "Rendered PDF report",
                    style={
                        "fontSize": "0.78rem",
                        "fontWeight": "800",
                        "color": "#c4b5fd",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.08em",
                    },
                ),
                rx.el.p(
                    rx.cond(
                        ComposeState.has_published_report,
                        "This preview is rendering the saved PDF from your public report.",
                        "Render the A4 report here, then create a public link when you are ready to save and share it.",
                    ),
                    style={"margin": "4px 0 0", "fontSize": "0.84rem", "color": "#9ca3af", "lineHeight": "1.45"},
                ),
                style={"minWidth": "220px", "flex": "1"},
            ),
            rx.el.button(
                fomantic_icon("sync", size=14),
                rx.el.span(" Render PDF", style={"marginLeft": "6px"}),
                id="me-render-pdf-button",
                on_click=rx.call_script(
                    "(async function(){ "
                    "console.info('[materialized] Render PDF button clicked'); "
                    "if (window.__meRenderPdfInPage) await window.__meRenderPdfInPage(); "
                    "else console.error('[materialized] __meRenderPdfInPage missing'); "
                    "})()"
                ),
                class_name="ui primary button",
                style={"fontSize": "0.86rem", "padding": "9px 14px", "whiteSpace": "nowrap"},
            ),
            rx.el.button(
                fomantic_icon("file pdf outline", size=14),
                rx.el.span(" Download PDF (A4)", style={"marginLeft": "6px"}),
                on_click=rx.call_script("window.__meDownloadPdf && window.__meDownloadPdf()"),
                class_name="ui button",
                style={"fontSize": "0.86rem", "padding": "9px 14px", "whiteSpace": "nowrap"},
            ),
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "gap": "12px",
                "flexWrap": "wrap",
                "marginBottom": "10px",
            },
        ),
        rx.el.div(
            rx.el.div(
                "Click Render PDF to preview the generated A4 report here.",
                style={
                    "color": "#6b7280",
                    "fontSize": "0.92rem",
                    "fontWeight": "700",
                    "textAlign": "center",
                    "padding": "28px 12px",
                },
            ),
            id="me-report-pdf-viewer",
            role="region",
            aria_label="Rendered personal enhancement PDF report",
            style={
                "width": "100%",
                "border": "1px solid rgba(167, 139, 250, 0.38)",
                "borderRadius": "12px",
                "backgroundColor": "#e5e7eb",
                "boxShadow": "0 18px 38px rgba(2, 6, 23, 0.28)",
                "overflowX": "hidden",
                "padding": "18px",
                "boxSizing": "border-box",
            },
        ),
        rx.el.div(
            id="report-pdf-feedback",
            style={
                "minHeight": "18px",
                "marginTop": "8px",
                "fontSize": "0.82rem",
                "fontWeight": "700",
                "color": "#16a085",
                "textAlign": "center",
            },
        ),
        style={
            "padding": "10px",
            "border": "1px solid rgba(148, 163, 184, 0.24)",
            "borderRadius": "10px",
            "backgroundColor": "rgba(15, 23, 42, 0.35)",
            "marginBottom": "10px",
        },
    )


def _share_qr_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                "SHARE QR",
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "700",
                    "color": "#cbd5e1",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                    "marginBottom": "6px",
                },
            ),
            rx.el.div(
                id="report-qr",
                style={
                    "width": "5.75rem",
                    "height": "5.75rem",
                    "backgroundColor": "#ffffff",
                    "border": "1px solid rgba(167, 139, 250, 0.42)",
                    "borderRadius": "8px",
                    "padding": "4px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.cond(
                    ComposeState.has_published_report,
                    "Public share link",
                    "Shareable link",
                ),
                style={"fontSize": "0.82rem", "fontWeight": "700", "color": "#c4b5fd"},
            ),
            rx.cond(
                ComposeState.has_published_report,
                rx.el.div(
                    ComposeState.report_public_url,
                    style={
                        "fontSize": "0.72rem",
                        "color": "#cbd5e1",
                        "marginTop": "6px",
                        "fontFamily": "'SFMono-Regular', Menlo, Consolas, monospace",
                        "wordBreak": "break-all",
                        "maxWidth": "100%",
                    },
                ),
                rx.cond(
                    ComposeState.report_publishing,
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                class_name="ui active mini inline loader",
                                style={"marginRight": "6px"},
                            ),
                            rx.el.span(
                                "Generating public link...",
                                style={"color": "#94a3b8", "fontSize": "0.78rem"},
                            ),
                            style={"display": "flex", "alignItems": "center", "minWidth": "0"},
                        ),
                        rx.el.button(
                            "Reset",
                            type="button",
                            on_click=ComposeState.reset_report_publish,
                            class_name="ui mini button",
                            style={
                                "padding": "5px 9px",
                                "fontSize": "0.72rem",
                                "fontWeight": "800",
                                "marginLeft": "8px",
                            },
                        ),
                        style={"display": "flex", "alignItems": "center", "marginTop": "6px", "flexWrap": "wrap"},
                    ),
                    rx.el.div(
                        _generate_public_link_button(),
                        rx.el.div(
                            "Creates a shareable public link with your report, model, and share card.",
                            style={
                                "fontSize": "0.72rem",
                                "color": "#64748b",
                                "marginTop": "6px",
                                "lineHeight": "1.3",
                            },
                        ),
                        style={"marginTop": "8px"},
                    ),
                ),
            ),
            rx.cond(
                ComposeState.report_publish_error != "",
                _inline_notice(ComposeState.report_publish_error, size=11),
                rx.fragment(),
            ),
            style={"flex": "1", "minWidth": "180px", "overflow": "hidden"},
        ),
        style={
            "display": "flex",
            "alignItems": "flex-start",
            "gap": "14px",
            "width": "100%",
            "padding": "10px",
            "border": "1px solid rgba(148, 163, 184, 0.24)",
            "borderRadius": "8px",
            "backgroundColor": "rgba(15, 23, 42, 0.35)",
        },
    )



def _report_hidden_inputs() -> rx.Component:
    """Hidden inputs feeding data to client-side JS (PDF/PNG/share). Always mounted."""
    return rx.el.div(
        rx.el.input(
            id="report-card-mode",
            value=ComposeState.share_card_mode,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-canonical-base",
            value="",
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-share-path",
            value=ComposeState.share_url,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-published-url",
            value=ComposeState.report_public_url,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-pdf-url",
            value=ComposeState.report_pdf_url,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-share-name",
            name="me-report-share-name",
            auto_complete="off",
            value=ComposeState.input_personal_tag,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-share-seed",
            value=ComposeState.param_seed,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-share-points",
            value=ComposeState.param_points,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-userpic-data-url",
            value=ComposeState.report_portrait_data_url,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.textarea(
            id="report-character-note",
            value=ComposeState.report_character_note,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-export-categories",
            value=ComposeState.export_categories_csv,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-export-animals",
            value=ComposeState.export_animals_summary,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.textarea(
            id="report-export-animals-json",
            value=ComposeState.export_animals_json,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.textarea(
            id="report-export-composition-genes-json",
            value=ComposeState.export_composition_genes_json,
            read_only=True,
            style={"display": "none"},
        ),
        rx.el.input(
            id="report-export-genes",
            value=ComposeState.export_gene_names_csv,
            read_only=True,
            style={"display": "none"},
        ),
        rx.cond(
            (ComposeState.materialization_artifact_tab == "report")
            | (ComposeState.materialization_artifact_tab == "share")
            | ComposeState.report_publishing,
            _report_hidden_capture_content(),
            rx.fragment(),
        ),
    )


def _share_action_button(icon_name: str, label: str, bg: str, js_call: str) -> rx.Component:
    _circle: dict = {
        "width": "52px",
        "height": "52px",
        "borderRadius": "999px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "cursor": "pointer",
        "transition": "transform 0.15s, box-shadow 0.15s",
        "boxShadow": "0 4px 14px rgba(0,0,0,0.25)",
        "background": bg,
    }
    return rx.el.div(
        rx.el.div(
            fomantic_icon(icon_name, size=22, color="#ffffff"),
            on_click=rx.call_script(js_call),
            style=_circle,
        ),
        rx.el.div(
            label,
            style={
                "fontSize": "0.68rem",
                "color": "#cbd5e1",
                "marginTop": "5px",
                "textAlign": "center",
                "fontWeight": "600",
            },
        ),
        style={"display": "flex", "flexDirection": "column", "alignItems": "center"},
        title=label,
    )


def _profile_ai_link(link: rx.Var) -> rx.Component:
    return rx.el.a(
        rx.el.span(
            rx.el.img(
                src=link["icon_src"],
                alt="",
                width="24",
                height="24",
                style={
                    "width": "24px",
                    "height": "24px",
                    "display": "block",
                },
            ),
            style={
                "width": "36px",
                "height": "36px",
                "borderRadius": "999px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "background": "#f8fafc",
                "border": "1px solid rgba(148, 163, 184, 0.38)",
                "boxShadow": "0 2px 7px rgba(0, 0, 0, 0.2)",
            },
        ),
        rx.el.span(
            link["label"],
            style={
                "fontSize": "0.68rem",
                "fontWeight": "700",
                "color": "#cbd5e1",
            },
        ),
        href=link["url"],
        target="_blank",
        rel="noopener noreferrer",
        aria_label="Explain this profile with " + link["label"],
        title="Imagine and explain this profile with " + link["label"],
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "gap": "3px",
            "minWidth": "54px",
            "textDecoration": "none",
        },
    )


def _profile_ai_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            fomantic_icon("comments outline", size=17, color="#c4b5fd"),
            rx.el.span(
                "Describe and draw your enhanced character with AI",
                style={
                    "fontSize": "0.94rem",
                    "fontWeight": "900",
                    "color": "#f3f0ff",
                    "whiteSpace": "nowrap",
                },
            ),
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
            },
        ),
        rx.el.div(
            rx.foreach(ComposeState.profile_ai_links, _profile_ai_link),
            style={
                "display": "flex",
                "justifyContent": "flex-start",
                "gap": "10px",
                "flexWrap": "wrap",
            },
        ),
        id="profile-ai-panel",
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "gap": "14px",
            "flexWrap": "wrap",
            "width": "fit-content",
            "maxWidth": "100%",
            "margin": "2px auto 12px",
            "padding": "9px 12px",
            "borderRadius": "10px",
            "border": "1px solid rgba(167, 139, 250, 0.3)",
            "background": "rgba(76, 29, 149, 0.16)",
        },
    )


def _share_section_body() -> rx.Component:
    """Share tab: auto-generated card image + social buttons, no gating."""
    _card_image_style = {
        "width": "auto",
        "maxWidth": "100%",
        "borderRadius": "14px",
        "border": "2px solid rgba(196, 181, 253, 0.42)",
        "boxShadow": "0 16px 40px rgba(15, 23, 42, 0.38)",
        "display": "block",
        "margin": "0 auto",
    }
    _spinner_box_style = {
        "textAlign": "center",
        "padding": "48px 16px",
        "borderRadius": "14px",
        "border": "1px dashed rgba(167, 139, 250, 0.35)",
        "background": "rgba(15, 23, 42, 0.25)",
        "marginBottom": "16px",
    }
    return rx.el.div(
        rx.cond(
            ComposeState.has_stl,
            rx.el.div(
                # ── Card image or spinner ────────────────────────────────
                rx.cond(
                    ComposeState.has_share_card,
                    rx.el.div(
                        rx.el.img(
                            src=ComposeState.share_card_src,
                            alt="Your shareable enhancement card",
                            style=_card_image_style,
                        ),
                        # Card mode toggle
                        rx.el.div(
                            rx.el.button(
                                fomantic_icon("exchange", size=14),
                                rx.el.span(
                                    rx.cond(
                                        ComposeState.is_character_card,
                                        " Switch to 3D model card",
                                        " Switch to character card",
                                    ),
                                    style={"marginLeft": "4px"},
                                ),
                                on_click=ComposeState.toggle_share_card_mode,
                                class_name="ui mini button",
                                style={
                                    "background": "rgba(124, 58, 237, 0.22)",
                                    "color": "#c4b5fd",
                                    "border": "1px solid rgba(167, 139, 250, 0.38)",
                                    "borderRadius": "8px",
                                    "cursor": "pointer",
                                    "fontSize": "0.78rem",
                                },
                            ),
                            style={"textAlign": "center", "marginTop": "8px"},
                        ),
                        style={"marginBottom": "18px"},
                    ),
                    rx.el.div(
                        rx.cond(
                            ComposeState.share_card_generating,
                            rx.el.div(
                                rx.el.div(
                                    class_name="ui active small inline loader",
                                    style={"marginRight": "10px"},
                                ),
                                rx.el.span(
                                    "Preparing your share card...",
                                    style={"color": "#c4b5fd", "fontSize": "0.95rem"},
                                ),
                                style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
                            ),
                            rx.el.div(
                                fomantic_icon("share alternate", size=28, color="#c4b5fd"),
                                rx.el.p(
                                    "Switch to this tab to generate your share card.",
                                    style={"margin": "8px 0 0", "color": "#94a3b8", "fontSize": "0.88rem"},
                                ),
                            ),
                        ),
                        style=_spinner_box_style,
                    ),
                ),
                # ── Row 1: Save / Copy actions ─────────────────────────
                rx.el.div(
                    _share_action_button("download", "Save image", "#7c3aed",
                                         "window.__meDownloadPng && window.__meDownloadPng()"),
                    _share_action_button("copy", "Copy link", "#7c3aed",
                                         "window.__meCopyShareLink && window.__meCopyShareLink()"),
                    _share_action_button("file pdf outline", "Save PDF report", "#7c3aed",
                                         "window.__meDownloadPdf && window.__meDownloadPdf()"),
                    style={
                        "display": "flex",
                        "gap": "18px",
                        "justifyContent": "center",
                        "marginTop": "4px",
                    },
                ),
                # ── Row 2: Social media share ─────────────────────────
                rx.el.div(
                    rx.el.div(
                        "Share on social media",
                        style={
                            "fontSize": "0.72rem",
                            "color": "#94a3b8",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.08em",
                            "fontWeight": "700",
                            "textAlign": "center",
                            "marginBottom": "8px",
                        },
                    ),
                    rx.el.div(
                        _share_action_button("twitter", "X", "#1DA1F2",
                                             "window.__meShareIntent && window.__meShareIntent('twitter')"),
                        _share_action_button("facebook", "Facebook", "#1877F2",
                                             "window.__meShareIntent && window.__meShareIntent('facebook')"),
                        _share_action_button("linkedin", "LinkedIn", "#0A66C2",
                                             "window.__meShareIntent && window.__meShareIntent('linkedin')"),
                        _share_action_button("whatsapp", "WhatsApp", "#25D366",
                                             "window.__meShareIntent && window.__meShareIntent('whatsapp')"),
                        _share_action_button("telegram plane", "Telegram", "#26A5E4",
                                             "window.__meShareIntent && window.__meShareIntent('telegram')"),
                        style={
                            "display": "flex",
                            "gap": "18px",
                            "justifyContent": "center",
                            "flexWrap": "wrap",
                        },
                    ),
                    style={"marginTop": "12px"},
                ),
                rx.el.div(
                    id="report-copy-feedback",
                    style={
                        "fontSize": "0.82rem",
                        "color": "#16a085",
                        "textAlign": "center",
                        "marginTop": "8px",
                        "minHeight": "18px",
                        "fontWeight": "600",
                    },
                ),
                # ── QR + share link panel ──────────────────────────────
                _share_qr_panel(),
                # ── Published report links (after Create public link) ──
                _published_report_links(),
            ),
            rx.el.p(
                "Generate a 3D model first, then come back here to share your enhancements.",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
        ),
    )


def _report_section_body() -> rx.Component:
    """Report/export contents: PDF viewer, portrait upload, and report customization."""
    return rx.el.div(
        rx.cond(
            ComposeState.has_stl,
            rx.el.div(
                rx.cond(
                    ComposeState.is_shared_visit,
                    rx.fragment(),
                    rx.script(
                        """
                        setTimeout(function () {
                          if (window.__meRenderActiveReportPdfInPage) {
                            window.__meRenderActiveReportPdfInPage();
                          }
                        }, 0);
                        """
                    ),
                ),
                _report_pdf_viewer_panel(),
                _report_portrait_upload_panel(),
            ),
            rx.el.p(
                "Generate a 3D model first, then come back here to build your personal enhancement report.",
                style={"color": "#9ca3af", "fontSize": "0.88rem", "textAlign": "center", "padding": "16px"},
            ),
        ),
    )



_COLLAPSIBLE_STYLE: dict = {
    "borderRadius": "8px",
    "border": "1px solid rgba(148, 163, 184, 0.24)",
    "padding": "4px 10px 10px",
    "backgroundColor": "rgba(15, 23, 42, 0.58)",
    "marginBottom": "10px",
}


def _sculpture_right_pane() -> rx.Component:
    return rx.el.div(
        # Hidden textarea — always in DOM so the viewer iframe can read it
        rx.el.textarea(
            value=ComposeState.stl_base64,
            id="stl-b64-data",
            style={"display": "none"},
        ),
        # Offscreen capture iframe — always mounted, re-runs whenever viewer_nonce changes
        _report_capture_iframe(),
        _choice_section(),
        _sculpture_section(),
    )


def _sculpture_tab() -> rx.Component:
    return rx.el.div(
        _rpg_materialize_layout(),
        style={
            "width": "100%",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "stretch",
        },
    )


# ── Tab navigation ───────────────────────────────────────────────────────────

_RPG_ROUTES: set[str] = {"/", "/materialization", "/about", "/knowledgebase"}


def _tab_link(route: str, icon: str, label: str, active_route: str) -> rx.Component:
    return rx.el.a(
        fomantic_icon(icon, size=18),
        rx.el.span(f" {label}", style={"marginLeft": "8px"}),
        class_name="active item" if route == active_route else "item",
        href=route,
    )


def _disabled_materialization_tab() -> rx.Component:
    return rx.el.span(
        fomantic_icon("atom", size=18),
        rx.el.span(" Materialization", style={"marginLeft": "8px"}),
        class_name="disabled item",
        title="Materialize selected genes first.",
        style={
            "opacity": "0.42",
            "cursor": "not-allowed",
            "pointerEvents": "auto",
        },
    )


def _tab_menu(active_route: str) -> rx.Component:
    return rx.el.div(
        _tab_link("/", "user", "Character profile", active_route),
        (
            _tab_link("/materialization", "atom", "Materialization", active_route)
            if active_route == "/materialization"
            else rx.cond(
                ComposeState.materialization_tab_enabled,
                _tab_link("/materialization", "atom", "Materialization", active_route),
                _disabled_materialization_tab(),
            )
        ),
        _tab_link("/knowledgebase", "book", "Knowledgebase", active_route),
        _tab_link("/about", "home", "About", active_route),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Real Genes · Real Science · Your Character · ",
                    style={"color": "#94a3b8"},
                ),
                rx.el.span(
                    "Printable Crystal From Your Genes",
                    style={"color": "#a78bfa", "fontWeight": "900"},
                ),
                style={
                    "height": "100%",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "background": "none",
                    "cursor": "default",
                    "pointerEvents": "none",
                    "fontSize": "0.92rem",
                    "letterSpacing": "0.04em",
                    "textTransform": "uppercase",
                    "padding": "0 1.5em",
                },
            ),
            *(
                [
                    rx.el.a(
                        fomantic_icon("github", size=16, color="#94a3b8"),
                        href=GITHUB_PROJECT_URL,
                        target="_blank",
                        rel="noopener noreferrer",
                        title="View source on GitHub",
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "padding": "0 0.75em",
                            "height": "100%",
                            "opacity": "0.7",
                            "transition": "opacity 0.2s",
                        },
                    ),
                ]
                if GITHUB_PROJECT_URL
                else []
            ),
            class_name="right menu",
        ),
        class_name="ui top attached tabular menu",
        id="me-top-tab-menu",
    )


def _inline_notice(text: rx.Var, size: int = 12) -> rx.Component:
    return rx.el.div(
        fomantic_icon("circle-alert", size=size, color="#fca5a5"),
        rx.el.span(text, style={"marginLeft": "6px"}),
        style={
            "display": "flex",
            "alignItems": "center",
            "marginTop": "6px",
            "padding": "6px 10px",
            "borderRadius": "8px",
            "fontSize": "0.78rem",
            "fontWeight": "700",
            "lineHeight": "1.35",
            "backgroundColor": "rgba(15, 23, 42, 0.6)",
            "border": "1px solid rgba(248, 113, 113, 0.48)",
            "color": "#fca5a5",
        },
    )


def _global_notice_toast() -> rx.Component:
    is_error = ComposeState.notice_kind == "error"
    is_hint = ComposeState.notice_kind == "hint"
    accent = rx.cond(is_error, "#fca5a5", rx.cond(is_hint, "#86efac", "#fde68a"))
    icon_name = rx.cond(is_hint, "info circle", "circle-alert")
    return rx.cond(
        ComposeState.notice_kind == "warning",
        rx.fragment(),
        rx.el.div(
            fomantic_icon(icon_name, size=14, color=accent),
            rx.el.span(ComposeState.notice_text, style={"marginLeft": "8px"}),
            style={
                "position": "fixed",
                "left": "75%",
                "bottom": "28px",
                "zIndex": 2000,
                "display": "flex",
                "alignItems": "center",
                "maxWidth": "min(90vw, 440px)",
                "padding": "12px 18px",
                "borderRadius": "10px",
                "fontSize": "0.9rem",
                "fontWeight": "700",
                "lineHeight": "1.35",
                "boxShadow": "0 12px 32px rgba(2, 6, 23, 0.38)",
                "backgroundColor": "rgba(15, 23, 42, 0.84)",
                "border": rx.cond(
                    is_error,
                    "1px solid rgba(248, 113, 113, 0.48)",
                    rx.cond(
                        is_hint,
                        "1px solid rgba(134, 239, 172, 0.48)",
                        "1px solid rgba(251, 191, 36, 0.48)",
                    ),
                ),
                "color": accent,
                "transition": "opacity 0.5s ease, transform 0.5s ease",
                "opacity": rx.cond(ComposeState.notice_visible, 1, 0),
                "transform": rx.cond(
                    ComposeState.notice_visible,
                    "translate(-50%, 0)",
                    "translate(-50%, 12px)",
                ),
                "pointerEvents": rx.cond(ComposeState.notice_visible, "auto", "none"),
            },
        ),
    )


def _materialize_hint_bubble(anchor: str) -> rx.Component:
    text = (
        ComposeState.materialize_name_missing_notice
        if anchor == "name"
        else ComposeState.materialize_genes_warning_notice
    )
    visible = (
        ComposeState.name_warning_visible
        if anchor == "name"
        else ComposeState.genes_warning_visible
    )
    position_style = (
        {
            "position": "fixed",
            "left": "24px",
            "bottom": "28px",
            "marginTop": "0",
            "zIndex": 1500,
            "maxWidth": "320px",
        }
        if anchor == "genes"
        else {
            "position": "absolute",
            "top": "100%",
            "left": "0",
            "marginTop": "6px",
            "zIndex": 60,
            "maxWidth": "320px",
        }
    )
    return rx.cond(
        text,
        rx.el.div(
            fomantic_icon("circle-alert", size=13, color="#fde68a"),
            rx.el.span(text, style={"marginLeft": "7px"}),
            style={
                **position_style,
                "display": "flex",
                "alignItems": "center",
                "padding": "9px 12px",
                "borderRadius": "9px",
                "fontSize": "0.8rem",
                "fontWeight": "700",
                "lineHeight": "1.35",
                "boxShadow": "0 12px 32px rgba(2, 6, 23, 0.38)",
                "backgroundColor": "rgba(15, 23, 42, 0.92)",
                "border": "1px solid rgba(251, 191, 36, 0.48)",
                "color": "#fde68a",
                "transition": "opacity 0.3s ease",
                "opacity": rx.cond(visible, 1, 0),
                "pointerEvents": "none",
            },
        ),
        rx.fragment(),
    )


def _tab_page(active_route: str, content: rx.Component) -> rx.Component:
    is_rpg_route = active_route in _RPG_ROUTES
    is_profile_route = active_route == "/"
    segment_class_name = (
        "ui bottom attached segment me-rpg-profile-page"
        if is_profile_route
        else "ui bottom attached segment"
    )
    tab_theme_css = rx.el.style(
        """
        #me-top-tab-menu.ui.top.attached.tabular.menu {
            background: #020617 !important;
            border-color: rgba(124, 58, 237, 0.42) !important;
            border-radius: 0 !important;
        }
        @media (max-width: 1150px) {
            #me-top-tab-menu .right.menu {
                display: none !important;
            }
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .item {
            color: #cbd5e1 !important;
            border-color: transparent !important;
            font-size: 1.25rem !important;
            padding: 1.05em 1.35em !important;
            min-height: 3.6rem !important;
            display: inline-flex !important;
            align-items: center !important;
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .item:hover {
            background: rgba(124, 58, 237, 0.16) !important;
            color: #f8fafc !important;
        }
        #me-top-tab-menu.ui.top.attached.tabular.menu .active.item {
            background: #0f172a !important;
            color: #c4b5fd !important;
            border-color: rgba(124, 58, 237, 0.72) !important;
            font-weight: 800 !important;
        }
        @media (hover: none) and (pointer: coarse) {
            #me-top-tab-menu.ui.top.attached.tabular.menu {
                display: flex !important;
                overflow-x: auto !important;
                scrollbar-width: none;
            }
            #me-top-tab-menu.ui.top.attached.tabular.menu::-webkit-scrollbar {
                display: none;
            }
            #me-top-tab-menu.ui.top.attached.tabular.menu .item {
                flex: 1 0 auto !important;
                justify-content: center !important;
                min-height: 3rem !important;
                padding: 0.72rem 0.55rem !important;
                font-size: 0.86rem !important;
                line-height: 1.05 !important;
                white-space: nowrap !important;
            }
        }
        #me-rpg-tab-segment.ui.bottom.attached.segment {
            background: #020617 !important;
            border-color: rgba(124, 58, 237, 0.42) !important;
            border-radius: 0 !important;
        }
        html:has(#me-rpg-tab-segment),
        body:has(#me-rpg-tab-segment) {
            background: #020617 !important;
        }
        #me-app-content:has(#me-rpg-tab-segment) {
            background: #020617 !important;
            padding: 0 !important;
        }
        html:has(.me-rpg-profile-page),
        body:has(.me-rpg-profile-page) {
            overflow-x: hidden;
            overflow-y: hidden;
            background: #020617 !important;
        }
        #me-app-content:has(.me-rpg-profile-page) {
            height: 100svh !important;
            min-height: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            background: #020617 !important;
        }
        #me-app-content:has(.me-rpg-profile-page) > .ui.fluid.container {
            height: 100svh;
            min-height: 0;
            display: flex;
            flex-direction: column;
        }
        .me-rpg-profile-page {
            flex: 1 1 auto;
            min-height: 0;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden;
            border-left: 0 !important;
            border-right: 0 !important;
            border-bottom: 0 !important;
            border-radius: 0 !important;
        }
        .me-rpg-profile-page > .me-rpg-shell {
            height: calc(100svh - 3.6rem) !important;
            min-height: 0 !important;
            padding: 8px 12px 10px !important;
            border-radius: 0 !important;
            overflow: hidden;
        }
        .me-rpg-profile-page .me-rpg-dashboard {
            height: 100%;
            min-height: 0;
            overflow-x: auto;
            overflow-y: hidden;
            align-items: stretch;
            scrollbar-width: thin;
        }
        .me-rpg-profile-page .me-rpg-left-panel {
            position: static;
            align-self: stretch;
        }
        .me-rpg-profile-page .me-rpg-library-section {
            height: 100%;
            max-height: 100%;
            min-height: 0;
        }
        .me-rpg-profile-page .me-rpg-center-panel,
        .me-rpg-profile-page .me-rpg-body-map-panel {
            min-height: 0;
        }
        .me-rpg-profile-page .me-rpg-center-panel {
            height: 100%;
            max-height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            scrollbar-width: thin;
            scrollbar-gutter: stable;
        }
        .me-rpg-profile-page .me-rpg-body-map-panel {
            display: flex;
            flex-direction: column;
            min-height: 100%;
        }
        .me-rpg-profile-page .me-rpg-body-stage {
            flex: 1 1 auto;
            height: auto;
            min-height: clamp(640px, min(84svh, 70vw), 900px) !important;
            padding-top: 0;
            padding-bottom: 96px;
        }
        .me-rpg-profile-page .me-rpg-body-image {
            height: clamp(570px, min(78svh, 66vw), 850px) !important;
        }
        @media (max-height: 820px) {
            .me-rpg-profile-page .me-rpg-center-panel {
                max-height: calc(100svh - 4.2rem);
                padding-right: 4px;
            }
            .me-rpg-profile-page .me-rpg-body-stage {
                min-height: clamp(620px, 82svh, 760px) !important;
                padding-bottom: 88px !important;
            }
            .me-rpg-profile-page .me-rpg-body-image {
                height: clamp(540px, 76svh, 700px) !important;
                max-width: min(100%, 680px) !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-leg-cta {
                position: sticky;
                left: auto;
                bottom: 16px;
                transform: none;
                align-self: center;
                width: max-content;
                max-width: calc(100% - 24px);
                margin-top: 12px;
                margin-bottom: 10px;
            }
        }
        @media (min-width: 1200px) and (max-height: 900px) and (orientation: landscape) {
            .me-rpg-profile-page .me-rpg-body-stage {
                min-height: clamp(600px, calc(100svh - 13rem), 720px) !important;
                padding: 2px 14px 82px !important;
                justify-content: center !important;
            }
            .me-rpg-profile-page .me-rpg-body-image {
                height: clamp(500px, calc(100svh - 19rem), 620px) !important;
                max-width: min(100%, 720px) !important;
            }
        }
        @media (orientation: portrait) and (min-width: 900px) {
            .me-rpg-profile-page .me-rpg-body-stage {
                min-height: clamp(820px, min(84svh, 92vw), 1180px) !important;
                padding: 0 18px 78px !important;
                justify-content: center !important;
            }
            .me-rpg-profile-page .me-rpg-body-image {
                height: clamp(720px, min(76svh, 72vw), 1040px) !important;
                max-width: min(100%, 920px) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--expression,
            .me-rpg-profile-page .me-rpg-body-marker--perception {
                top: 23% !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--longevity-genome,
            .me-rpg-profile-page .me-rpg-body-marker--stress-resistance {
                top: 51% !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--environmental-adaptation,
            .me-rpg-profile-page .me-rpg-body-marker--regeneration {
                top: 70% !important;
            }
        }
        @media (min-width: 1800px) and (min-height: 1100px) {
            .me-rpg-profile-page .me-rpg-body-stage {
                min-height: clamp(980px, 74svh, 1160px) !important;
                padding-bottom: 112px !important;
            }
            .me-rpg-profile-page .me-rpg-body-image {
                height: clamp(900px, 69svh, 1080px) !important;
                max-width: min(100%, 1040px) !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-leg-button {
                min-width: 300px !important;
                min-height: 68px !important;
                font-size: clamp(1.6rem, 1.4vw, 2.05rem) !important;
            }
        }
        @media (hover: none) and (pointer: coarse) {
            html:has(.me-rpg-profile-page),
            body:has(.me-rpg-profile-page) {
                overflow-x: hidden !important;
                overflow-y: auto !important;
                background: #020617 !important;
                scroll-behavior: smooth;
            }
            #me-app-content:has(.me-rpg-profile-page) {
                height: auto !important;
                min-height: 100svh !important;
                overflow: visible !important;
                padding: 0 !important;
                background: #020617 !important;
            }
            #me-app-content:has(.me-rpg-profile-page) > .ui.fluid.container {
                height: auto !important;
                min-height: 100svh !important;
                display: block !important;
            }
            .me-rpg-profile-page {
                min-height: 100svh !important;
                overflow: visible !important;
                border-radius: 0 !important;
            }
            .me-rpg-profile-page > .me-rpg-shell {
                height: auto !important;
                min-height: 100svh !important;
                padding: 0 !important;
                border-radius: 0 !important;
                overflow: visible !important;
            }
            .me-rpg-profile-page .me-rpg-dashboard {
                display: flex !important;
                flex-direction: column !important;
                height: auto !important;
                min-height: 100svh !important;
                max-height: none !important;
                overflow: visible !important;
                gap: 0 !important;
                align-items: stretch !important;
            }
            .me-rpg-profile-page .me-rpg-center-panel {
                order: 1;
                flex: 0 0 auto !important;
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                height: auto !important;
                max-height: none !important;
                overflow: visible !important;
                padding: 0 !important;
                scrollbar-gutter: auto !important;
            }
            .me-rpg-profile-page .me-mobile-budget-stack {
                position: sticky !important;
                top: 0 !important;
                z-index: 35 !important;
                width: 100% !important;
                margin: 0 0 12px 0 !important;
                padding: 0 0 8px 0 !important;
                box-sizing: border-box !important;
                background: #020617 !important;
                box-shadow: 0 12px 24px rgba(2, 6, 23, 0.88) !important;
                pointer-events: none !important;
            }
            .me-rpg-profile-page .me-mobile-budget-stack .me-budget-gauge {
                position: static !important;
                top: auto !important;
                margin-bottom: 8px !important;
                background: #0f172a !important;
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
                pointer-events: auto !important;
            }
            .me-rpg-profile-page .me-orientation-block {
                width: 100% !important;
                padding: 10px 12px 8px !important;
            }
            .me-rpg-profile-page .me-orientation-headline {
                font-size: 1.02rem !important;
                line-height: 1.3 !important;
                margin-bottom: 6px !important;
            }
            .me-rpg-profile-page .me-orientation-body {
                font-size: 0.84rem !important;
                line-height: 1.4 !important;
                margin-bottom: 6px !important;
            }
            .me-rpg-profile-page .me-orientation-help {
                min-height: 48px !important;
            }
            .me-rpg-profile-page .me-mobile-budget-materialize {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                position: static !important;
                top: auto !important;
                bottom: auto !important;
                z-index: auto !important;
                width: 100% !important;
                padding: 0 0 2px 0 !important;
                margin: 0 0 12px 0 !important;
                box-sizing: border-box !important;
                background: #020617 !important;
                pointer-events: none !important;
            }
            .me-rpg-profile-page .me-mobile-budget-materialize--hidden {
                display: none !important;
            }
            .me-rpg-profile-page .me-mobile-budget-materialize .me-rpg-materialize-leg-cta {
                position: relative !important;
                left: auto !important;
                bottom: auto !important;
                transform: none !important;
                width: min(92vw, 440px) !important;
                max-width: calc(100vw - 24px) !important;
                z-index: auto !important;
                padding: 8px !important;
                border-radius: 30px !important;
                background: #020617 !important;
                box-shadow: 0 10px 22px rgba(2, 6, 23, 0.82) !important;
                pointer-events: auto !important;
            }
            .me-rpg-profile-page .me-mobile-budget-materialize .me-rpg-materialize-credit-line {
                background: #0f172a !important;
            }
            .me-rpg-profile-page .me-rpg-left-panel {
                order: 2;
                flex: 0 0 auto !important;
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                position: relative !important;
                top: auto !important;
                align-self: stretch !important;
                box-sizing: border-box !important;
            }
            .me-rpg-profile-page .me-rpg-library-section {
                height: auto !important;
                max-height: none !important;
                min-height: 0 !important;
                overflow: visible !important;
                padding: 12px 10px calc(28px + env(safe-area-inset-bottom, 0px)) !important;
                box-sizing: border-box !important;
            }
            .me-rpg-profile-page .me-rpg-library-panel {
                width: 100% !important;
                padding: 12px !important;
                box-sizing: border-box !important;
            }
            .me-rpg-profile-page .me-rpg-library-grid,
            .me-rpg-profile-page .me-rpg-category-gene-grid {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
            .me-rpg-profile-page .me-rpg-category-gene-grid {
                padding-left: 10px !important;
                margin-left: 4px !important;
                border-left: 3px solid rgba(124, 58, 237, 0.45) !important;
            }
            .me-rpg-profile-page .me-budget-gauge {
                position: sticky !important;
                top: 0 !important;
                z-index: 30 !important;
                width: 100% !important;
                border-radius: 14px !important;
            }
            .me-rpg-profile-page .me-rpg-sidebar-intro {
                width: 100% !important;
            }
            .me-rpg-profile-page .me-rpg-body-map-panel {
                min-height: calc(100svh - 3.6rem) !important;
                height: auto !important;
                display: flex !important;
                flex-direction: column !important;
                position: relative !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
            .me-rpg-profile-page .me-rpg-body-map-title {
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                z-index: 7 !important;
                max-width: none !important;
                width: calc(100% - 20px) !important;
                margin: 8px auto 0 !important;
                padding: 9px 10px !important;
                border: 1px solid rgba(167, 139, 250, 0.30) !important;
                background: rgba(15, 23, 42, 0.78) !important;
                box-shadow: 0 12px 30px rgba(2, 6, 23, 0.34) !important;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
            }
            .me-rpg-profile-page #compose-personal-tag {
                min-height: 44px !important;
                padding: 10px 13px !important;
                font-size: 1rem !important;
                border-radius: 12px !important;
            }
            .me-rpg-profile-page .me-rpg-body-stage {
                flex: none !important;
                width: 100% !important;
                height: calc(100svh - 3.6rem - 130px) !important;
                min-height: 560px !important;
                max-height: none !important;
                padding: 18px 0 24px !important;
                justify-content: center !important;
                overflow: hidden !important;
                box-sizing: border-box !important;
            }
            .me-rpg-profile-page .me-rpg-body-stage::before {
                inset: 8% 14% 7% !important;
                filter: blur(18px) !important;
            }
            .me-rpg-profile-page .me-rpg-body-stage::after {
                inset: 18% 35% 9% !important;
                filter: blur(26px) !important;
            }
            .me-rpg-profile-page .me-rpg-body-image {
                height: min(62svh, 540px) !important;
                max-height: calc(100svh - 3.6rem - 270px) !important;
                width: auto !important;
                max-width: min(88vw, 460px) !important;
                object-fit: contain !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker {
                width: 150px !important;
                height: 124px !important;
                transform: translate(-50%, -50%) scale(0.94) !important;
                z-index: 4 !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker:hover {
                transform: translate(-50%, -50%) scale(1) !important;
            }
            .me-rpg-profile-page .me-rpg-marker-orbit-shell {
                width: 150px !important;
                height: 124px !important;
            }
            .me-rpg-profile-page .me-rpg-marker-gene-orbit {
                display: none !important;
            }
            .me-rpg-profile-page .me-rpg-marker-icon-node {
                width: 56px !important;
                height: 56px !important;
                background: rgba(15, 23, 42, 0.84) !important;
            }
            .me-rpg-profile-page .me-rpg-marker-icon-node i.icon {
                font-size: 52px !important;
            }
            .me-rpg-profile-page .me-rpg-marker-count-badge {
                min-width: 24px !important;
                height: 24px !important;
                font-size: 0.74rem !important;
            }
            .me-rpg-profile-page .me-rpg-marker-label {
                top: calc(50% + 38px) !important;
                padding: 5px 8px !important;
                max-width: 156px !important;
                white-space: normal !important;
                border-radius: 8px !important;
                background: rgba(15, 23, 42, 0.82) !important;
                font-size: 0.88rem !important;
                line-height: 1.1 !important;
            }
            .me-rpg-profile-page .me-rpg-marker-label span:first-child {
                font-size: 0.92rem !important;
                white-space: normal !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--expression {
                top: 24% !important;
                left: calc(50% - min(34vw, 190px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--perception {
                top: 24% !important;
                left: calc(50% + min(34vw, 190px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--longevity-genome {
                top: 50% !important;
                left: calc(50% - min(33vw, 180px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--stress-resistance {
                top: 50% !important;
                left: calc(50% + min(33vw, 180px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--environmental-adaptation {
                top: 76% !important;
                left: calc(50% - min(34vw, 190px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-marker--regeneration {
                top: 76% !important;
                left: calc(50% + min(34vw, 190px)) !important;
            }
            .me-rpg-profile-page .me-rpg-body-stage > .me-rpg-materialize-leg-cta {
                display: none !important;
            }
            .me-rpg-profile-page .me-rpg-body-stage > .me-rpg-materialize-leg-cta.me-onboarding-materialize-lift {
                display: flex !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-credit-line {
                width: 100% !important;
                box-sizing: border-box !important;
                font-size: 0.74rem !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-credit-line span:last-child {
                display: none !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-leg-button {
                width: 100% !important;
                min-width: 0 !important;
                min-height: 56px !important;
                padding: 14px 18px !important;
                font-size: clamp(1.1rem, 5.2vw, 1.45rem) !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-alert-stack {
                width: 100% !important;
                max-width: 100% !important;
            }
            .me-rpg-profile-page .me-rpg-materialize-alert {
                width: 100% !important;
            }
            .me-rpg-profile-page .me-onboarding-marker-hint .me-rpg-body-map-title,
            .me-rpg-profile-page .me-onboarding-marker-hint .me-rpg-body-image,
            .me-rpg-profile-page .me-onboarding-marker-hint .me-rpg-materialize-leg-cta {
                opacity: 0.18 !important;
            }
            .me-rpg-profile-page .me-onboarding-center-lift {
                z-index: 1010 !important;
            }
            .me-rpg-profile-page .me-onboarding-tip-card {
                position: fixed !important;
                left: 12px !important;
                right: 12px !important;
                top: max(12px, env(safe-area-inset-top, 0px)) !important;
                bottom: auto !important;
                transform: none !important;
                z-index: 1400 !important;
                width: auto !important;
                max-width: calc(100vw - 24px) !important;
                max-height: min(52svh, calc(100svh - 24px - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px))) !important;
                overflow-y: auto !important;
                overscroll-behavior: contain !important;
                padding: 10px 12px !important;
                margin: 0 !important;
                border-radius: 12px !important;
                box-shadow: 0 0 18px rgba(255, 255, 255, 0.52) !important;
            }
            .me-rpg-profile-page .me-onboarding-tip-card p {
                font-size: 0.88rem !important;
                line-height: 1.38 !important;
            }
            .me-rpg-profile-page .me-onboarding-tip-card p:first-of-type {
                font-size: 1rem !important;
                line-height: 1.24 !important;
                margin-bottom: 4px !important;
            }
            .me-rpg-profile-page .me-onboarding-tip-card button {
                width: 32px !important;
                height: 32px !important;
                border-radius: 9px !important;
            }
        }
        """
    )
    return template(
        tab_theme_css if is_rpg_route else rx.fragment(),
        _tab_menu(active_route),
        rx.el.div(
            content,
            class_name=segment_class_name,
            id="me-rpg-tab-segment" if is_rpg_route else "",
            style={
                "minHeight": "400px",
                "background": "#020617" if is_rpg_route else "#ffffff",
                "borderColor": "rgba(124, 58, 237, 0.42)" if is_rpg_route else "#e5e7eb",
                "padding": "0.85rem" if is_rpg_route else "1rem",
            },
        ),
        _global_notice_toast(),
        include_report_libs=active_route == "/materialization",
    )


# ── Pages ────────────────────────────────────────────────────────────────────


@rx.page(
    route="/",
    title=_page_title("/"),
    image=_page_image_url(),
    description=_page_description("/"),
    meta=_page_meta("/"),
    on_load=[AppState.redirect_legacy_tab, ComposeState.check_clean_storage],
)
def index_page() -> rx.Component:
    """Character profile — default RPG loadout builder."""
    return _tab_page("/", _rpg_active_genes_layout())


_NOINDEX_META: list[dict[str, str]] = [
    {"name": "robots", "content": "noindex, nofollow"},
]


@rx.page(
    route="/materialization",
    title=_page_title("/materialization"),
    image=_page_image_url(),
    description=_page_description("/materialization"),
    meta=_NOINDEX_META,
    on_load=[
        ComposeState.apply_artex_params,
        ComposeState.apply_saved_report,
        ComposeState.apply_shared_report,
    ],
)
def materialization_page() -> rx.Component:
    """Materialization — 3D output, viewer, report, and export actions."""
    return _tab_page("/materialization", _rpg_materialization_layout())


@rx.page(
    route="/about",
    title=_page_title("/about"),
    image=_page_image_url(),
    description=_page_description("/about"),
    meta=_page_meta("/about"),
    on_load=[AppState.redirect_legacy_tab],
)
def about_page() -> rx.Component:
    """About / landing page — fully static, SSR-friendly."""
    return _tab_page("/about", _rpg_about_layout())


@rx.page(
    route="/knowledgebase",
    title=_page_title("/knowledgebase"),
    image=_page_image_url(),
    description=_page_description("/knowledgebase"),
    meta=_page_meta("/knowledgebase"),
    on_load=[KnowledgebaseState.initialize],
)
def knowledgebase_page() -> rx.Component:
    """Enhancement knowledgebase — searchable genes / experiments / orgs explorer."""
    return _tab_page("/knowledgebase", knowledgebase_layout())