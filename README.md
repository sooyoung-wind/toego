# Toego

Toego(퇴고) revises Korean academic manuscripts written in Hangul Word Processor (`.hwp`) against
reviewer comments. It checks every sentence for claims that go beyond the paper's own results, unsupported
generalization, boilerplate phrasing, tense, and terminology; checks each paragraph's structure
(topic-first, conclusion-last, or both) for its position in the paper; traces the argument from the
introduction to the conclusion; and fact-checks every revised number against the manuscript's tables and
figures. The output is a single HTML page that shows each paragraph before and after revision, with a
reason for every edit and a copy button for pasting the revised text back into the manuscript.

## 무엇을 하나

한/글(.hwp) 학술 원고를 심사 의견에 맞춰 퇴고합니다.

1. **문장**: 결과로 뒷받침되지 않는 주장, 결과 범위를 넘는 일반화, AI 문장 같은 상투 표현, 시제, 주술 호응, 용어 통일
2. **문단**: 문장 간 인과·대조, 위치에 맞는 두괄식·미괄식·양괄식, 문단별 한 문장 요약
3. **절·장**: 요약을 이어 읽은 논증 흐름, 서론의 질문과 결론의 대응, 장·절 구조 제안
4. **초록**: 본문과 범위·수치가 같은지
5. **검증**: 수정안의 모든 수치를 원고 표·그림과 사용자가 지정한 근거 자료에 독립 대조
6. **결과물**: 수정 전/후 어절 비교, 수정 근거, 복사 버튼, 반영 체크가 있는 HTML 한 장

## 사용

```
/toego:revise 원고.hwp [근거 자료 폴더...]
```

심사 의견 원문을 같은 메시지에 붙여 넣으면 그 의견을 기준으로 검토합니다. 결과는 현재 디렉터리의
`toego/<원고 이름>/퇴고_비교.html`에 생깁니다.

구성 요소: skill `revise`, agent `sentence-auditor`(문장), `paragraph-auditor`(문단·흐름),
`fact-checker`(수치 대조), skill 폴더 안의 Python 스크립트 3개(`hwp_extract.py`, `lint_ko.py`,
`build_html.py`).

## 요구 사항

- **Claude Code에서 쓰는 것을 권장합니다.** 스크립트를 로컬에서 실행해야 하고, agent는 claude.ai 채팅에서 로드되지 않습니다.
- [`uv`](https://docs.astral.sh/uv/)와 Python 3.11(`uv`가 자동으로 받음).
- **입력은 저자 정보(이름·소속·이메일)를 뺀 심사용 원고입니다.** 저자 정보가 있으면 지우고 넣으세요. 원고에서 이메일 주소가 발견되면 추출기가 경고하고 작업을 멈춥니다.
- `.hwp`(HWP 5.x)만 지원합니다. `.hwpx`는 한/글에서 `.hwp`로 저장해서 쓰세요. 수식 개체는 텍스트로 추출되지 않습니다.

## 실행하는 것과 네트워크 사용 (공개)

- HWP 추출 시 `uv run --frozen --no-project`가 PyPI에서 다음 고정 버전 패키지를 임시 환경에 받습니다:
  `pyhwp==0.1b15`(AGPL-3.0, 별도 프로세스로 실행하며 이 저장소에 포함하지 않음), `six==1.17.0`,
  `lxml==6.1.3`, `beautifulsoup4==4.15.0`. 사용자 환경에 설치하지 않습니다.
- 린터와 HTML 빌더는 Python 표준 라이브러리만 씁니다.
- 원고와 추출 결과는 로컬 작업 폴더에만 기록합니다. plugin 자체는 원고 내용을 외부 서버로 보내지 않으며, hook·MCP 서버·자격 증명을 쓰지 않습니다. (Claude가 원고를 읽고 검토하는 것은 일반적인 Claude 사용과 같습니다.)
- 생성된 HTML은 외부 리소스를 불러오지 않는 단일 파일이며, "반영" 체크 상태만 브라우저 `localStorage`에 저장합니다.

원고는 미발표 자료일 수 있습니다. 결과 HTML을 외부에 게시할지는 사용자가 판단하세요.

## Privacy

See the [Privacy Policy](PRIVACY.md). The plugin is meant for anonymized review manuscripts without author names, affiliations, or emails. It runs locally, has no server, and sends no manuscript content anywhere.

## License

MIT
