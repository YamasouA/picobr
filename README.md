# picobr

## 使い方
```bash
python browser.py <url>
```

## 現状
- Schemes
    - http, https, file, view-source

- Redirect

- Entities（一部）


## 課題
- Chapter1
    - <script>が存在するhtmlファイルの表示
    - data schemeの表示
    - Cache-controlの再検討
    - data schemeの表示の時に、show_flagを使わなくていいようにする(多分bodyタグで囲めばいい)
## 参考
- https://browser.engineering
