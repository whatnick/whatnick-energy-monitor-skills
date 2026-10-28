---
name: whatnick-energy-monitor-elecrow-ordering
description: Package verified bare PCB fabrication files and obtain Elecrow quotations using an authenticated browser and Playwright. Use for Gerber/drill uploads, material and finish selection, per-design quantities, quote/cart verification, uploaded-file hash checks, and safe handoff before checkout or payment. Distinguish PCB fabrication from assembly and preserve account privacy.
compatibility: Python with Playwright and an installed Chromium browser; KiCad CLI for fabrication validation/export.
metadata:
  org: whatnick
  domain: pcb-manufacturing
---

# Elecrow bare-PCB quotation and ordering

Use the browser + Playwright for Elecrow fabrication submission, not email or
an invented private API. The verified entry point is
https://www.elecrow.com/pcb-manufacturing.html and the cart is
https://www.elecrow.com/checkout/cart.

## Authority and privacy

Separate quote/cart preparation, order placement, payment and manufacturing
authorization. A request to quote permits uploads and adding quoted jobs to
the cart, not checkout/payment or a production start. Stop at the requested
boundary. Do not describe a cart SKU as an order number or manual engineering
acceptance. Never clear an existing cart or delete unrelated items.

Use a task-specific persistent Chromium profile. Let the user sign in visibly;
do not request passwords in chat, extract ordinary browser cookies or copy
someone else's profile. A local CDP connection can reuse that task browser:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9234")
    page = browser.contexts[0].pages[0]
```

Port 9234 is only an example: use the actual task browser endpoint. Bind CDP
locally. Do not close the user's browser when disconnecting a short automation
command. Stop the task browser after handoff if it is no longer needed.

Do not commit profiles, cookies, credentials, raw account-page HTML, shipping
addresses or file-download URLs containing access keys. Capture a cropped cart
table rather than the account dashboard. Store only non-sensitive quote
specifications, prices, filenames, hashes and supplier SKU/reference identifiers.

## Prepare fabrication evidence

1. Use the actual validated saved board, not a render or stale fabrication ZIP.
   Run ERC and DRC with all severities and schematic parity where applicable.
   Inspect every report and keep baseline issues distinct; never call a failed
   check clean. Preserve user `.kicad_pro` and editor-local settings.
2. Derive finished dimensions from the Edge.Cuts polygon centreline. KiCad
   plot/job extents can include the outline stroke, overstating each dimension.
   Read actual thickness/layers and keep the original board unchanged.
3. Package one flat upload ZIP per unique design with top/bottom copper, mask,
   silk, sole outline and metric absolute Excellon drills. Use separate PTH and
   NPTH files with clear names; omit genuinely empty drill sets. Internal
   windows/slots must remain in the profile or proper drill/route output.
   Do not duplicate routing in conflicting files. Elecrow accepts ZIP/RAR up
   to 30 MB. RS-274-X Gerbers were successfully uploaded.
4. Include fabrication notes for finish, holes, contacts, tolerances, no artwork
   substitutions and no order marks on functional surfaces. Record raw ZIP
   SHA256 and per-member hashes. Validate archive CRC and drill content.
5. Use per-assembly multiplicities: two identical probe/guide PCBs means twice
   the probe quantity, not two different designs. A bundle containing several
   upload ZIPs is a handoff, not one uploadable PCB design.

Bare PCB only means no component procurement, assembly, BOM/CPL or stencil.
Choose requested solder-mask colour per order; **purple is not a global default**.
Choose finish for the function: flat exposed electrical contacts may require
ENIG rather than uneven HASL. Ordinary ENIG is not hard-gold wear qualification.

## Proven browser workflow

Inspect the live DOM before reusing selectors; the examples below were observed
on the Elecrow FR-4 form. Its scripts initialize on `window.onload`.
`domcontentloaded` alone is too early: selecting a file before the change handler
exists silently leaves the UI unchanged.

```python
page.goto(
    "https://www.elecrow.com/pcb-manufacturing.html",
    wait_until="load",
)
page.wait_for_function(
    '()=>window.jQuery && '
    'jQuery._data(document.querySelector("#pcbFile"),"events")?.change?.length>0'
)
with page.expect_file_chooser() as chooser:
    page.locator("#addGerber").click()
chooser.value.set_files(str(upload_zip.resolve()))
```

The upload requires login: selecting a ZIP while signed out redirects to
Customer Login. Resume after user authentication; do not loop or bypass it.
Confirm `.file_accept` contains the exact selected filename.

The Gerber preview service may report it cannot preview images. This does not
establish a malformed manufacturing ZIP, but it does not prove DFM either.
Keep the warning, manually enter the actual outline dimensions and verify the
uploaded archive later. Do not fix a preview by changing correct PCB geometry.

### Observed FR-4 controls

| Setting | Selector / action |
| --- | --- |
| FR-4 | `label[for=material1]` |
| Two layers | `label[for=model2]` |
| Width / height | Fill `#long`, `#wide`, then press Tab to emit change |
| Quantity dropdown | Click `#form1 .qty_de`, then its quantity label |
| Five / ten boards | `label[for=selCheck1]` / `label[for=selCheck11]` |
| One unique design per ZIP | `label[for=design1]` |
| 1.6 mm finished thickness | `label[for=thickness5]` |
| Green / purple mask | `label[for=color1]` / `label[for=color7]` |
| White silkscreen | `label[for=screen1]` |
| ENIG / immersion gold | `label[for=finish3]` |
| No castellations | `label[for=hole1]` |
| 1 oz outer copper | `label[for=weight1]` |
| Ordinary 3-5 working days | Select value `35` in `#formTime` |
| Destination country | Select actual destination code in `#formCountry` |
| Add quoted job | Exact button name `Add To Cart` |

Quantity choices are hidden until `.qty_de` opens the dropdown; `.sel_text`
does not exist. Use real labels rather than forcing hidden radio elements.
No-stencil state was shown by hidden `.check` and no stencil item in the cart;
inspect current UI rather than assuming a checkbox API.
Wait for asynchronous pricing and production-time options to settle. Verify
checked values and displayed dimensions/filename before adding each job.

## Verify server-side outcome

After adding, wait for `/checkout/cart`. For every intended job, locate its
`tbody.cart.item` row by exact ZIP filename. Require:

- Correct PCB quantity, dimensions, layers, finished thickness, mask/silk,
  surface finish and copper weight. Cart line quantity is normally one batch;
  PCB quantity is inside that batch's options. Do not multiply both.
- Correct file and unique design count; no assembly/stencil or unrelated additions.
- Cart SKU and actual discounted line price, currency and subtotal recorded.
  Shipping/tax remain provisional unless separately confirmed.
- Reloaded cart retains the jobs; inspect before retrying an ambiguous add so
  a timeout does not create duplicates.

When the cart offers a download link for the uploaded fabrication archive,
use that authenticated browser context to download it and compare its raw
SHA256 to the submitted ZIP. Do not print or commit the signed/access-key URL:

```python
row = page.locator("tbody.cart.item").filter(has_text=upload_zip.name)
link = row.get_by_role("link", name=upload_zip.name, exact=True)
response = page.request.get(link.get_attribute("href"))
assert response.ok
assert hashlib.sha256(response.body()).hexdigest() == expected_sha256
```

This proves the uploaded artifact matches; it is not supplier DFM approval.
Include critical fabrication requirements inside the ZIP even when the cart
has no notes field. Record whether a manual engineering review was actually
requested; an automatic cart price alone is not that request.

For quote-only tasks, leave the verified jobs in the authenticated cart and
report prices plus unpaid status. Never click checkout/order/payment merely
to obtain an order reference. Further actions require the corresponding user
authorization and a final check of addresses, quantities, costs and terms.
