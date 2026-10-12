# Tajikistan — legislation as Markdown (LawCodex)

Legislation of the Republic of Tajikistan (Ҷумҳурии Тоҷикистон) as Markdown, in Tajik (`tg/`,
state language; a few acts in Russian, `ru/`). Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**.

> **Partial corpus.** The official sources cannot be harvested directly (see below); this
> repository contains the legislation pages of the National Legislation Centre that were archived
> by the Internet Archive — the Constitution, all main codes and constitutional laws, and a part
> of the ordinary laws.

## Coverage

| Path | Contents | Files |
|---|---|---:|
| `tg/konstitutsiya/` | Constitution of 6 November 1994 (consolidated, incl. 2003 and 2016 amendments) | 1 |
| `tg/qonunhoi-konstitutsioni/` | Constitutional laws | 17 |
| `tg/kodeksho/` | Codes (Civil, Criminal, Tax, Labour, Land, Customs, procedure codes …) | 19 |
| `tg/qonunho/<year>/` | Laws | 237 |
| `ru/zakony/<year>/` | Laws whose archived mmk.tj page is in Russian | 8 |
| **Total** | | **282** |

Pages marked *Аз эътибор соқитшуда* (repealed) on mmk.tj — 2 codes and 12 laws — are excluded.

* Texts are the **consolidated versions** published by the National Legislation Centre under the
  President (Маркази миллии қонунгузории назди Президенти Ҷумҳурии Тоҷикистон, mmk.tj): amending
  laws are cited in brackets after each changed provision, and superseded wording is shown in
  italics as on the site (rendered as `*…*`).
* `status` comes from the page's "Ҳолат" field (*Амалкунанда* = in force); `last_amended` is the
  date of the Internet Archive capture used (the text as published on that day).

## Sources and why archives

* **mmk.tj** — National Legislation Centre; publishes the legislation of Tajikistan
  (Constitution, constitutional laws, codes, laws, …) with consolidated texts. The site does not
  answer from outside Tajikistan (TCP time-outs), so its pages were taken from the **Internet
  Archive Wayback Machine** (CDX listing of `mmk.tj/content/*` and `mmk.tj/node/*`, newest capture of
  each page; only Drupal nodes of type *legislation* are converted). Each file's
  `archived_source` is the Wayback URL.
* **adlia.tj / mmih.adlia.tj** — Centralized Bank of Legal Information "Adlia" of the Ministry of
  Justice. The old adlia.tj (FoxWeb) is broken; the new mmih.adlia.tj only shows the first few
  articles of each act without a (paid / registered) subscription ("Тарофаҳо"), so it was not used.
* Russian versions: only the few mmk.tj legislation pages that were published in Russian.

## Not covered / gaps

* Laws whose mmk.tj page was never archived (most ordinary laws), all acts of the last months, and
  Russian translations.
* Secondary legislation (presidential decrees, government resolutions).

Licence: under the Law of the Republic of Tajikistan "On Copyright and Related Rights", official
documents (laws, court decisions and other texts of a legislative, administrative and judicial
nature) are not objects of copyright.

## Structure

```
tg/konstitutsiya/                         Constitution
tg/qonunhoi-konstitutsioni/               constitutional laws
tg/kodeksho/                              codes
tg/qonunho/<year>/                        laws, by date of adoption
ru/zakony/<year>/                         laws published in Russian on mmk.tj
scripts/                                  fetch + convert code
```

File names: transliterated title + mmk.tj node id. Headings: part (қисм) / section (фасл) /
chapter (боб) / article (модда).

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/tj_wayback.py cdx       # -> ../_raw/tj/snapshots.tsv
python3 scripts/tj_wayback.py fetch     # -> ../_raw/tj/html/ (Internet Archive, slow)
python3 scripts/tj_convert.py
```
