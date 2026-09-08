# PharmaGenome design system

This records the implemented Phase 1 scientific workspace. It does not imply completed analytics or an approved image composition.

## Palette
| Role | Light | Dark |
|---|---|---|
| Canvas | #f4f6f5 | #10241e |
| Surface | #ffffff | #182f27 |
| Ink | #193731 | #e3efe8 |
| Secondary text | #526860 | #b0c3b8 |
| Border | #dce4df | #355145 |
| Accent | #146b54 | #9bd6b9 |
| Soft accent | #e8f1eb | #274939 |
| Sidebar | #fafbf9 | #12291f |
| Warning | #735323 | #e4c68a |

Theme uses root data-theme and local-storage persistence. Status always includes text.

## Typography
Bundled Manrope Variable for headings and inventory numerals; IBM Plex Sans Variable for body, controls and annotations. Main heading clamps from 25–34px with 650 weight and -0.035em tracking. Panel headings are 17px/700; body is 14px, panel descriptions 12px, metadata 10–12px. Inventory numerals and timestamps use tabular figures. Long explanations remain within 65ch.

## Layout and components
Desktop: fixed 246px navigation rail, 75px topbar, main content capped at 1560px with 38px horizontal padding. The primary collection/model split is 1.45:1; secondary panels are equal columns. Five inventory values form a ruled row.
Panels use 12px radii, 24px padding and one-pixel borders without shadows. Compact shadcn-derived buttons use 6px radii and 39px minimum height. Lucide outline icons form a single consistent icon vocabulary.
The semantic dataset table scrolls inside its wrapper. Source plans appear separately from imported records. The relationship diagram is explicitly a schema model.

## Responsive behavior
At 1160px the rail narrows to 218px and content padding to 24px. At 900px panels stack and relationship steps use two columns. At 650px navigation becomes a 260px drawer, main padding is 18px, panels have 20px padding, inventory wraps 3+2, and relationship steps return to one column.
The table retains a 540px minimum width inside horizontal overflow. The page itself must not overflow.

## Interaction and accessibility
Active navigation exposes aria-current. The theme toggle names its next action. A skip link targets main content. Focus uses a two-pixel accent outline offset five pixels.
Closed mobile navigation is inert. Opening moves focus into the dialog, makes background content inert and locks scrolling. Tab wraps, Escape closes, and focus returns to the trigger. A backdrop closes the drawer.
Only controls, loading feedback and drawer movement animate. Reduced motion disables transitions and animation.

## Scientific honesty
Unavailable counts are an em dash, never zero. Empty-collection claims require a ready database response. Source plans are labeled Planned; quality remains Not measured until validated reports exist. Fixtures must be identified. System exports are infrastructure snapshots, not scientific results.
Keep source/version evidence, phase disclosures and the research-use limitation visible. Do not add invented charts, diagnoses, treatment suggestions or implied biological findings.

## Verification scope
An independent reviewer inspected desktop/mobile screenshots and code, then marked the unknown-data and keyboard-navigation fixes resolved. CI covers those fixes. Live Chrome checks covered database connection, navigation, theme, mobile drawer and Escape behavior. No image-comp fidelity claim is made.
