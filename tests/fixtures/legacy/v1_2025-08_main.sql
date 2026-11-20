BEGIN TRANSACTION;
CREATE TABLE plate_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part1 TEXT NOT NULL,
            part2 TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            note TEXT,
            UNIQUE(part1, part2, phone_number)
        );
INSERT INTO "plate_info" VALUES(1,'ABC','1234','0912345678','老客戶');
INSERT INTO "plate_info" VALUES(2,'DEF','5678','0923456789','');
INSERT INTO "plate_info" VALUES(3,'ABC','1234','0988777666','第二支電話');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('plate_info',3);
COMMIT;
