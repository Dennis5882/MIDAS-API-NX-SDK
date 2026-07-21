# midas-nx 시작 가이드 (프로그래밍이 처음이신 분도 괜찮습니다)

이 가이드는 MIDAS Gen NX/Civil NX를 실무에서 쓰시지만 Python이나 프로그래밍은
처음이신 구조 엔지니어를 위한 것입니다. Python 설치부터 첫 스크립트 실행까지,
한 번에 끝까지 따라 할 수 있도록 순서대로 안내합니다.

> 개발 경험이 있으시다면 [README.md](../../README.md)의 Quick Start가 더 빠릅니다.
> 이 가이드는 그 전 단계 — "Python이 뭔지도 잘 모르겠다"는 분들을 위한 것입니다.

## 시작하기 전에 필요한 것

- Windows PC (이 가이드는 Windows 기준으로 설명합니다)
- MIDAS Gen NX 또는 Civil NX 설치 및 정상 라이선스
- 인터넷 연결 (MIDAS 클라우드 릴레이 서버를 통해 통신합니다)

## 1단계: Python 설치하기

1. https://www.python.org/downloads/ 에 접속합니다.
2. "Download Python 3.x.x" 버튼을 눌러 설치 파일을 내려받습니다.
3. 설치 파일을 실행합니다. **이때 설치 화면 맨 아래의 "Add python.exe to PATH"
   체크박스를 반드시 체크**한 뒤 "Install Now"를 누르세요. 이 체크를 빠뜨리면
   나중에 명령 프롬프트가 `python`을 인식하지 못합니다.
4. 설치가 끝나면 확인해봅니다. 시작 메뉴에서 "cmd"를 검색해 명령 프롬프트를 열고
   다음을 입력하세요.

   ```
   python --version
   ```

   `Python 3.x.x` 같은 결과가 나오면 설치 성공입니다. `'python'은 내부 또는
   외부 명령... 이 아닙니다` 같은 오류가 뜨면 3번의 PATH 체크를 빠뜨린 것이니
   Python을 다시 설치해보세요.

## 2단계: midas-nx 설치하기

같은 명령 프롬프트에서 다음을 입력합니다.

```
pip install midas-nx
```

`Successfully installed midas-nx-...`라는 메시지가 뜨면 설치 완료입니다.

## 3단계: MAPI 키 발급받기

`MAPI-Key`는 이 SDK가 MIDAS Gen NX/Civil NX와 통신할 때 쓰는 인증 키로,
Python이 아니라 **MIDAS Gen NX(또는 Civil NX) 프로그램 안에서** 직접
발급받습니다.

1. MIDAS Gen NX(또는 Civil NX)를 실행합니다.
2. 상단 메뉴에서 **Open API** 관련 메뉴(버전에 따라 "Open API" 또는 "Apps"라는
   이름으로 나타납니다)를 찾아 들어갑니다.
3. **API Key 발급**을 선택하면 긴 문자/숫자 조합의 키가 화면에 나타납니다.
   이 키를 복사해두세요.

> 이 키는 프로그램이 켜져 있는 동안만 유효한 임시 키입니다. 언제든 같은
> 메뉴에서 다시 발급받을 수 있으니 잃어버려도 걱정하지 마세요.

## 4단계: 첫 스크립트 작성하고 실행하기

메모장(또는 VS Code 등 아무 텍스트 편집기)을 열어 아래 내용을 그대로
붙여넣습니다. `"여기에_3단계에서_복사한_키_붙여넣기"` 부분만 실제 키로
바꿔주세요.

```python
from midas_nx import MidasClient, Product, doc
from midas_nx.db.node_element import Element, Node
from midas_nx.db.project import Unit
from midas_nx.db.properties.material import Material
from midas_nx.db.properties.section import Section

# Civil NX를 쓰신다면 product=Product.CIVIL로 바꾸세요.
client = MidasClient(mapi_key="여기에_3단계에서_복사한_키_붙여넣기", product=Product.GEN)

doc.new_project(client=client)
Unit.update({1: {"DIST": "M", "FORCE": "KN"}}, client=client)

Material.create(
    {1: {"TYPE": "CONC", "NAME": "C24",
         "PARAM": [{"P_TYPE": 1, "STANDARD": "KS01(RC)", "DB": "C24"}]}},
    client=client,
)
Section.create(
    {1: {"SECTTYPE": "DBUSER", "SECT_NAME": "Column",
         "SECT_BEFORE": {"USE_SHEAR_DEFORM": True, "SHAPE": "SB", "DATATYPE": 2,
                          "SECT_I": {"vSIZE": [0.6, 0.6]}}}},
    client=client,
)
Node.create({1: {"X": 0, "Y": 0, "Z": 0}, 2: {"X": 0, "Y": 0, "Z": 3.2}}, client=client)
Element.create({1: {"TYPE": "BEAM", "MATL": 1, "SECT": 1, "NODE": [1, 2]}}, client=client)
doc.save(client=client)

print("성공! Gen NX 화면에서 기둥이 생성된 걸 확인해보세요.")
```

파일 이름은 `first_script.py`로 저장합니다 (바탕화면이나 원하는 폴더 어디든
괜찮습니다).

명령 프롬프트에서 저장한 폴더로 이동한 뒤 실행합니다. 예를 들어 바탕화면에
저장했다면:

```
cd Desktop
python first_script.py
```

`성공! Gen NX 화면에서...`이 출력되고, Gen NX 창으로 전환해보면 0.6m × 0.6m
콘크리트 기둥(높이 3.2m) 하나가 새로 생성되어 있을 겁니다.

> 위 예제의 재료(`C24`/`KS01(RC)`) 조합은 2026-07-22에 실제 Gen NX·Civil NX
> 세션에서 라이브로 검증됐습니다 (자세한 내용은
> [docs/live_verification_notes.md](../live_verification_notes.md) 참고) —
> 첫 스크립트가 반드시 동작하도록 임의의 예시가 아니라 확인된 값을 사용했습니다.

## 잘 안 될 때

- **`MidasConnectionError`가 뜬다면**: Gen NX/Civil NX가 실행 중인지, Open API가
  연결되어 있는지 확인하세요. 이 SDK의 에러 메시지는 끝에 `(Hint: ...)` 형태로
  무엇을 확인해야 하는지 알려줍니다.
- **`MidasAuthError`가 뜬다면**: 3단계에서 복사한 키를 스크립트에 정확히
  붙여넣었는지 확인하세요. 키는 프로그램을 껐다 켜면 바뀔 수 있으니, 안 되면
  다시 발급받아 붙여넣어 보세요.
- **회사 방화벽 안에 있다면**: [README.md](../../README.md)의 "Troubleshooting"
  섹션에 IT팀에 전달할 방화벽 허용 정보(포트/주소)가 정리되어 있습니다.

## 다음 단계

- **AI 코딩 도구와 함께 확장하기**: 위 스크립트의 패턴만 익히면, 이후로는 직접
  모든 코드를 외워서 쓸 필요가 없습니다. Claude Code·ChatGPT·GitHub Copilot 같은
  AI 도구에 이 스크립트를 보여주고 "기둥 대신 20m 보를 만들어줘", "하중조합을
  추가해줘"처럼 자연어로 요청하면 됩니다. AI가 실제 `midas-nx` 코드로 바꿔줄
  겁니다 — 이 SDK는 애초에 그렇게 함께 쓰기 편하도록 설계되었습니다(타입 힌트,
  명확한 에러 메시지 등).
- 더 실무에 가까운 예제: GitHub의 [`examples/python/`](../../examples/python/)
  폴더 (보 하중조합, 풍하중, 시공단계 등) — AI에게 "이 예제처럼 만들어줘"라고
  보여줘도 좋습니다.
- 구현된 전체 기능 목록: [ROADMAP.md](../../ROADMAP.md)
- 더 자세한 사용법·설계 원칙: [README.md](../../README.md)

이 가이드를 따라 하다 막히는 부분이 있었다면 GitHub Issues에 알려주세요 —
다음 사용자를 위해 가이드를 개선하는 데 큰 도움이 됩니다.
