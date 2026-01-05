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

GithubCopilot君に作らせただけなので多分バグとかいっぱいある。
DLSite/Fanza/Boothだと発行イベントうまく取れなかったり作者名拾えなかったりするからとらメロンを最優先にしてる。

やってること自体は各サイトで誌名で検索して最初の作品を拾うだけなので、
まあまあの高確率で関係ない作品のURLを拾ってくる。特にBooth。
精度上げたいけどあんまり難しいことはできそうにないのでとりあえずこのまま使って手動チェックしてるけどめんどくさいからもう少しなんとかしたいね。
