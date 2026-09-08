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

## Phase 2 populated states
Retain the forest/sage Operate workspace and existing shadcn-derived table/button controls. Replace the empty collection only when a ready API provides a dataset. Show source/fixture status, assembly, cohort scope, sample observations and distinct variants with different labels. Quality reports distinguish accepted, excluded, invalid and duplicate records; no accuracy claim derives from acceptance fraction. Use responsive definition lists and wrapping checksums; long inventories scroll inside the table. Report download failures display a retryable message. Source connections distinguish an imported subset from planned adapters. Both themes and 390px/1440px views are covered by browser checks.

## Phase 3 genomic explorers
Add Genomics, Gene explorer and Variant explorer to the existing rail. All use the same Apply/Reset filter form and data response. Keep controls native, labels visible and loading/error/empty states distinct. Ranked frequency bars use a fixed 0–100% axis, no entrance animation, Recharts keyboard support, exact table values and accessible gene drill-down buttons. Variant details open inline; mobile tables scroll within their container. The mutation matrix uses source-coded sample labels and text equivalents for observation/coverage state. Match light/dark semantic tokens and retain reduced-motion behavior. Export labels specify JSON and paginated row scope. No invented full names, clinical interpretations or drug/pathway metadata.
