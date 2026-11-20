# Develop

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
NEWAGAIN_DATA_DIR=/tmp/cw python start.py                    # never use real shop data
python -m pytest -q -p no:cacheprovider tests                # data + offscreen UI flow tests
python tools/make_fake_data.py /tmp/cw/洗車資料.db            # ~1 year, 150 customers
NEWAGAIN_DATA_DIR=/tmp/cw QT_QPA_PLATFORM=offscreen python tools/screenshot.py /tmp/shots
QT_QPA_PLATFORM=offscreen python tools/bench.py               # large-data timings
```

- `make_fake_data.py` writes `加入假資料前備份_<time>.db` next to the db first.
- A screenshot run that "hangs" at low CPU = a modal dialog opened offscreen;
  wrap with `faulthandler.dump_traceback_later(60, exit=True)`.
- To test an upgrade from an old version: build a db with the old schema (see
  `ORIGINAL_SCHEMA` / `V11_SCHEMA` in tests) and put it next to the exe as `database.db`.
