# Shipping Routes

Auto-selected by destination country in `etsy_orders.py`. Override with `--method <CODE>`.

| Code    | Name                                  | Countries          |
|---------|---------------------------------------|--------------------|
| `FZZXR` | YunExpress Clothing Economy           | US + all others    |
| `THPHR` | YunExpress Economy (Unrestricted)     | EU + CH (see list) |

**EU country set** (triggers `THPHR`):
DE FR GB NL BE AT CH IT ES SE DK NO FI PL PT CZ HU RO SK SI

To see the full route catalog for any destination:
```bash
python3 fulfill.py --list-methods --country <ISO2>
```

## Common API error codes

| Code   | Meaning                              | Fix                                      |
|--------|--------------------------------------|------------------------------------------|
| `1001` | Auth failed                          | Check `YUN_CUSTOMER_CODE` / `YUN_API_SECRET` in `.env` |
| `1002` | Order number already exists          | Duplicate receipt — already submitted    |
| `2001` | Invalid shipping method code         | Run `--list-methods` to find valid code  |
| `2003` | Weight out of range                  | Adjust `UnitWeight` in `etsy_orders.py`  |
| `2010` | Required field missing               | Check Receiver fields in dry-run output  |
