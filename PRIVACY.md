# Privacy Policy — Toego

Last updated: 2026-10-01

## Summary

Toego is a Claude Code plugin that runs on your own computer. It has no server, collects no telemetry,
and does not send your data to the plugin author or to any third party.

## What the plugin reads

- The manuscript file (`.hwp`) you give it. A manuscript may contain personal data such as author
  names, affiliations, and email addresses.
- Any evidence folders you point it to (for example, result tables or response drafts), read only to
  check the numbers in the revision.

## What the plugin stores, and where

The plugin writes only to a work folder under your current directory (`./toego/<manuscript name>/`):
a copy of the manuscript (`extract/src.hwp`), the extracted text, tables, captions and embedded
images, a lint report, the revision data (`review.json`), and the comparison HTML.

These files stay on your computer until you delete them. Deleting the work folder removes everything
the plugin created. The comparison HTML saves only its "applied" checkbox states in your browser's
`localStorage`.

## What the plugin sends

- The plugin itself sends no manuscript content, personal data, or usage data anywhere.
- When extracting a `.hwp` file, `uv` downloads fixed versions of open-source Python packages
  (`pyhwp`, `six`, `lxml`, `beautifulsoup4`) from PyPI. These requests contain only package names
  and versions.
- Claude reads and reviews your manuscript as part of your normal Claude session. That processing is
  governed by your agreement with Anthropic and Anthropic's privacy policy, not by this plugin.

## Retention

The plugin author receives and retains no data. Local files remain until you delete them.

## Children

The plugin is intended for researchers and manuscript authors and is not directed at users under 18.

## Contact

Questions or requests: open an issue at https://github.com/sooyoung-wind/toego/issues

---

## 개인정보 처리방침 (요약)

Toego는 사용자 컴퓨터에서 실행되는 Claude Code plugin입니다. 서버가 없고, 사용 기록을 수집하지 않으며,
사용자 데이터를 개발자나 제3자에게 보내지 않습니다.

- **읽는 것:** 사용자가 지정한 원고(.hwp)와 근거 자료 폴더. 원고에는 저자 이름·소속·이메일 같은 개인정보가 들어 있을 수 있습니다.
- **저장하는 것:** 현재 디렉터리 아래 `./toego/<원고 이름>/`에 원고 사본, 추출 결과, 퇴고 데이터, 비교 HTML. 사용자가 삭제할 때까지 로컬에만 남습니다.
- **보내는 것:** plugin 자체는 아무것도 보내지 않습니다. HWP 추출 시 `uv`가 PyPI에서 고정 버전 패키지를 받으며, 이 요청에는 패키지 이름과 버전만 들어갑니다. Claude가 원고를 읽는 것은 일반적인 Claude 사용과 같고 Anthropic의 정책을 따릅니다.
- **보관:** 개발자는 어떤 데이터도 받거나 보관하지 않습니다.
- **문의:** https://github.com/sooyoung-wind/toego/issues
