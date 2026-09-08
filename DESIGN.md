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

## Phase 4 sequence workspace
Retain the forest/sage research identity. Use shadcn-derived textareas with explicit labels, single-record file input and IBM Plex Mono for sequences and numerical matrices. Tabs support arrow keys. Input changes clear stale results. Show scoring, base denominators, limits and synthetic example disclosure next to the controls. Alignments and matrices scroll inside keyboard-focusable regions; exports preserve complete results. Desktop/mobile light/dark evidence and independent finish review passed.

## Phase 5 research associations

Extend the forest/sage workspace with existing light/dark semantic tokens (--bg, --surface, --ink, --muted, --line, --accent, --soft), bordered panels, shadcn-derived buttons/tables and Lucide icons. Retain Manrope headings, IBM Plex Sans controls and IBM Plex Mono network identifiers.

Stack filters, snapshot provenance/export, four summary counts, focused association network, drug catalogue, pathway overlap and methods. Native labeled controls cover snapshot, drug query/type, source stage, disease and ordering; gene checkboxes require at least one selection. Apply commits draft filters and resets result pagination; pending changes are announced. Loading, retryable errors and empty results remain explicit.

The network shows one selected gene between up to three pathways and three drugs from the current result pages. Selecting a node or table link opens inline evidence, moves keyboard focus and scrolls to the detail. Drug details expose mechanisms, expandable disease labels and distinct source reports paginated ten at a time. Pathway details explain the selected-gene denominator. External links lead to source records; JSON export includes the response with its declared scope.

Filters change from three columns to two at 1000px and one at 650px. Mobile summaries use two columns; the network stacks with its gene first and removes connector strokes. Source actions and pagination wrap, while tables retain contained horizontal scrolling. Inputs and inline details receive accent focus outlines; existing reduced-motion behavior applies.

Keep snapshot/fixture identity, retrieval date, checksum, computation time, revision and limitations visible. Source stage is historical metadata; report counts do not establish efficacy, pathway overlap is not enrichment, and network links do not predict variant response or cohort treatment.



## Phase 6 statistical workbench

Extend the established forest/sage Operate workspace with a Statistics destination for measurements, 2 × 2 counts and pathway enrichment. Reuse native labeled inputs, shadcn-derived buttons and tables, restrained bordered panels, Manrope headings, IBM Plex Sans controls and IBM Plex Mono for submitted values, gene symbols, hashes and computational identifiers.

Measurement controls cover six declared methods, units or measurement context, and two to six groups or paired vectors. Count controls offer two-sided Fisher exact and chi-square without Yates correction through a semantic 2 × 2 table. Enrichment controls expose the source snapshot and gene checkboxes inside an explicitly restricted ten-gene universe. Arrow keys plus Home and End navigate the analysis tabs. Input changes clear stale results; synthetic examples remain labeled as teaching values rather than biological measurements.

Present successful results in a fixed evidence hierarchy: interpretation first; test statistic, unadjusted p-value and named effect estimate next; then uncertainty, descriptive values, restrained empirical-distribution or paired-observation charts, expected counts where applicable, and finally hypotheses, assumptions, limitations and provenance. Enrichment replaces the test metrics with universe, selected-gene, complete-family and primary BY-rejection counts, followed by all pathway tests ranked by BY q and raw p. Tables remain inside horizontally scrollable containers and pathway results paginate twenty rows at a time. Charts do not animate, state what each mark or step represents, and direct users to the JSON export for exact or overlapping values.

Loading uses explicit status text while source options load or a computation runs. Source failures use an alert with a retry action; validation and computation failures identify the request as the problem and tell the user to edit and rerun. Results remain absent until a successful response, and focus moves to the result heading when one arrives. A zero-rejection enrichment result receives an explanatory state rather than an empty biological claim.

At 650px, paired form fields stack, tabs wrap, the three result metrics become a vertical ruled list, and empirical distributions change from two columns to one. Result headings and export actions stack through the shared responsive pattern. Count and result tables retain contained horizontal scrolling so the page itself does not overflow. Desktop and 390px layouts preserve the same evidence order in light and dark themes.

Keep scientific scope inseparable from the result. Measurement uploads are computed by the research API but not stored; exports disclose that they contain the submitted inputs. Enrichment states its restricted imported universe, includes zero-overlap pathways in the correction family, treats BY as the primary multiplicity correction and reports BH as secondary context. Never present a non-significant result as evidence of no relationship, a pathway overlap as genome-wide enrichment, a p-value as effect size, or an acceptance count as scientific validity. Label unavailable estimates as not estimable. Preserve method version, computation time, SciPy and NumPy versions, code revision, input or source SHA-256, source retrieval time, complete parameters, assumptions and limitations in the exported result.


## Phase 7 drug-response modeling

Extend the established forest/sage scientific workspace with a Drug response destination presented as a pinned CellMiner NCI-60 experimental ledger. Reuse restrained bordered panels, compact native controls, shadcn-derived buttons and tables, Manrope headings, IBM Plex Sans body text and IBM Plex Mono for dataset versions, model identifiers, checksums and revisions. Keep activity direction, cohort size, feature count and evaluation scope visible beside the controls.

Arrange the workflow as dataset ledger, model specification, mutation-stratified response evidence, evaluation summary, held-out discrimination evidence, feature context and methods/provenance. Controls expose one drug, one fixed model family and a declared subset of the ten-gene panel. Evaluation values remain typographically restrained and show multiple metrics with descriptive variability; they must never resemble clinical risk scores. Charts and compact evidence blocks carry exact context, while explanatory text states what each target, threshold and split represents.

Loading, source failure, validation failure and computation failure use explicit status text and actionable retry or correction guidance. A successful run moves focus to the result heading. Native labels remain visible, keyboard focus uses the shared accent outline, status never depends on color, and reduced-motion behavior follows the existing workspace rule. Disabled actions communicate the minimum feature requirement.

On wide screens, keep the pinned dataset ledger beside model specification and place results in a clear vertical hierarchy. At narrower widths, paired regions and metric rows stack without changing evidence order. At 650px, controls and result actions stack or wrap, the final F1 metric spans the complete last row, and charts and evidence panels fit the viewport so the page itself never overflows.

Keep the experimental boundary inseparable from every result. Label the source as a pinned CellMiner NCI-60 cell-line snapshot and define the response as compound-activity average z score, where higher values indicate greater sensitivity. State that the binary target uses an independently predeclared zero z-score boundary, folds are repeated and correlated, uncertainty is descriptive, models and hyperparameters were fixed before comparison, and no hyperparameter search was performed. Preserve source version, retrieval time, snapshot SHA-256, computation time, code revision, random seed, split strategy, complete parameters, library versions, metrics and limitations in the export. Never imply patient response, efficacy, safety, treatment suitability, clinical validation or individualized prediction.
