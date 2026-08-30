# searchDojin
同人誌名またはとらメロンのURLをもとに、サークル名・作者名・誌名・発行イベント・発行日と、DLSite/FANZA/Booth/とら/メロンの販売URLを拾ってこようとする

# 使い方
[python](https://www.python.org/downloads/)をインストールして、

```shell
py -m pip requests
py -m pip bs4
```
で必要なライブラリを放り込んだら、
入力ファイルに誌名か、とらorメロンのURLを1行1冊入力して、
pyファイル全部並べたフォルダからコマンドプロンプトで
python3 search.py (入力ファイル) > (出力ファイル)
ってする。

これが

<img width="552" height="69" alt="image" src="https://github.com/user-attachments/assets/d3d2ff8d-24a6-4541-9b35-66f9cb6fc79b" />

こうして

<img width="1095" height="58" alt="image" src="https://github.com/user-attachments/assets/08857c1e-c7b7-4902-8c81-edcc5fd82407" />

こうなる

<img width="1324" height="79" alt="image" src="https://github.com/user-attachments/assets/f7e52097-147d-4cc5-b6a8-d8a988f4a6f2" />

# 全体の流れ

```mermaid
flowchart TD
	S([開始]) --> I[Case入力に与えられた文字列]
	I --> N{入力はnull?}
	N -- Yes --> U[Usageを出力]
	U --> E([Exit])
	N -- No --> T{入力の種類}

	T -- Melonbooks URL --> M1[Melonbooks URLから
サークル名・作家名・誌名・発売日・イベントを取得]
	M1 --> M2[誌名で他の対象サイトを検索
第一候補URLを取得]
	M2 --> C1[取得した各サイトの誌名と
基準サイトの誌名を比較]

	T -- toranoana URL --> T1[toranoana URLから
サークル名・作家名・誌名・発売日・イベントを取得]
	T1 --> T2[誌名で他の対象サイトを検索
第一候補URLを取得]
	T2 --> C2[取得した各サイトの誌名と
基準サイトの誌名を比較]

	T -- DLSite URL --> D1[誌名で他の対象サイトを検索
第一候補URLを取得]
	D1 --> P1{Melonbooks URLが見つかった?}
	P1 -- Yes --> M1b[Melonbooks URLからメタデータを取得]
	P1 -- No --> P2{toranoana URLが見つかった?}
	P2 -- Yes --> T1b[toranoana URLからメタデータを取得]
	P2 -- No --> D2[DLSite URLからメタデータを取得]
	M1b --> C3[取得した各サイトの誌名と
DLSiteの誌名を比較]
	T1b --> C3
	D2 --> C3

	T -- FANZA URL --> F1[誌名で他の対象サイトを検索
第一候補URLを取得]
	F1 --> P3{Melonbooks URLが見つかった?}
	P3 -- Yes --> M2b[Melonbooks URLからメタデータを取得]
	P3 -- No --> P4{toranoana URLが見つかった?}
	P4 -- Yes --> T2b[toranoana URLからメタデータを取得]
	P4 -- No --> F2[FANZA URLからメタデータを取得]
	M2b --> C4[取得した各サイトの誌名と
FANZAの誌名を比較]
	T2b --> C4
	F2 --> C4

	T -- booth URL --> B1[誌名で他の対象サイトを検索
第一候補URLを取得]
	B1 --> P5{Melonbooks URLが見つかった?}
	P5 -- Yes --> M3b[Melonbooks URLからメタデータを取得]
	P5 -- No --> P6{toranoana URLが見つかった?}
	P6 -- Yes --> T3b[toranoana URLからメタデータを取得]
	P6 -- No --> B2[booth URLからメタデータを取得]
	M3b --> C5[取得した各サイトの誌名と
boothの誌名を比較]
	T3b --> C5
	B2 --> C5

	T -- Alicebooks URL --> A1[誌名で他の対象サイトを検索
第一候補URLを取得]
	A1 --> P7{Melonbooks URLが見つかった?}
	P7 -- Yes --> M4b[Melonbooks URLからメタデータを取得]
	P7 -- No --> P8{toranoana URLが見つかった?}
	P8 -- Yes --> T4b[toranoana URLからメタデータを取得]
	P8 -- No --> A2[Alicebooks URLからメタデータを取得]
	M4b --> C6[取得した各サイトの誌名と
Alicebooksの誌名を比較]
	T4b --> C6
	A2 --> C6

	T -- その他の文字列 --> X1[入力値で対象サイトを検索
第一候補URLを取得]
	X1 --> P9{Melonbooks URLが見つかった?}
	P9 -- Yes --> M5[Melonbooks URLからメタデータを取得]
	P9 -- No --> P10{toranoana URLが見つかった?}
	P10 -- Yes --> T5[toranoana URLからメタデータを取得]
	P10 -- No --> D5[DLSite URLからメタデータを取得]
	M5 --> P11{Melonbooks URLが見つかった?}
	T5 --> P12{toranoana URLが見つかった?}
	D5 --> P13{比較対象URLが見つかった?}
	P11 -- Yes --> C7[取得した各サイトの誌名と
Melonbooksの誌名を比較]
	P11 -- No --> P12
	P12 -- Yes --> C8[取得した各サイトの誌名と
toranoanaの誌名を比較]
	P12 -- No --> P13
	P13 -- Yes --> C9[取得した各サイトの誌名と
DLSiteの誌名を比較]

	C1 --> F{誌名の乖離が大きい?}
	C2 --> F
	C3 --> F
	C4 --> F
	C5 --> F
	C6 --> F
	C7 --> F
	C8 --> F
	C9 --> F
	F -- Yes --> R[該当URLを出力対象から除外]
	F -- No --> O[サークル名・作者名・誌名・発売日・イベントと
DLSite・FANZA・booth・toranoana・Melonbooks・AlicebooksのURLを出力]
	R --> O
	O --> E

	Sites[(検索対象サイト<br/>DLSite / FANZA / booth / toranoana / Melonbooks / Alicebooks)]
```

# 制約とか

DLSite/Fanza/Boothだと発行イベントうまく取れなかったり作者名拾えなかったりするからとらメロンを最優先にしてる。

# ToDoとか

GithubCopilot君に作らせただけなので多分バグとかいっぱいあるから見つけたら直したい。

僕が最終的にGoogleSpreadsheetで蔵書管理してるから張り付けやすいようにタブ区切りテキストを吐き出してるけど、jsonとかにした方が扱いやすくなったりするのかな？

でも検索精度がいまいちだからなあ。
やってること自体は各サイトで誌名で検索して最初の作品を拾うだけなので、まあまあの高確率で関係ない作品のURLを拾ってくる。特にBooth。
精度上げたいけどあんまり難しいことはできそうにないのでとりあえずこのまま使って手動チェックしてるけどめんどくさいからもう少しなんとかしたいね。

本当はGoogleSpreadsheetの情報を月イチとかでクロールして拾い直したりできるといいよね。たまに半年後に急にDLSiteで頒布開始とかもあるし。もっと言えばDLSiteはお気に入り登録してお気に入りフォルダ「購入済み」に移したい。どうしても手動でやってる。大変。
