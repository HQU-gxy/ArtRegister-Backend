## users

| name:text    | user_id:int |
| ------------ | -------------- |
| example_user | 114514         |

## art_pieces

| name:text     | piece_uid:text | creator_id:int | owner_id:int |
| ------------- | -------------- | -------------- | ------------ |
| example_piece | DEAD2333       | 114514         | 1919810      |

## transactions

| piece_uid:text | old_owner_id:int | new_owner_id:int | dt:datetime         |
| -------------- | ---------------- | ---------------- | ------------------- |
| DEAD2333       | 1919810          | 114514           | 2023-10-01 12:00:00 |


*All data is not nullable; all IDs are unsigned.*