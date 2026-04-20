# リポジトリ運用メモ

## Git フロー

- 作業ブランチでコミット後、**毎回 main にもプッシュする**
  - feature branch → main に fast-forward or cherry-pick → `git push origin main`
  - ユーザーから明示的に別ブランチ指定がない限り main を更新
