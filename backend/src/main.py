from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import src.core.schemas.schemas as _schemas
import src.core.services.services as _services
import src.core.metrics.hots_and_colds as hot_colds_metric
from typing import Dict
from src.settings import ENGINE_PSWD, DATA_FORMAT, SESSION_TIME, IGNORE_TICKERS, DATE_FORMAT
from datetime import datetime
from aiocache import cached
import sys
from src.core.database.mongo import Database, NotFoundException
from src.core.database.mongo.tickers import TickersDatabase
from src.core.database.mongo.users import UsersDatabase
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.connect()
    yield
    Database.close()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://52.200.228.178:3000",
    "http://fcitracker.online",
    "https://localhost:3000",
    "https://52.200.228.178:3000",
    "https://fcitracker.online",
    "http://18.235.24.52"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
                
@cached(ttl=SESSION_TIME)
async def execute_login(ip: str) -> datetime:
    user_database = UsersDatabase()
    try:
        user = await user_database.get_by_ip(ip)
    except NotFoundException:
        user = _schemas.User(ip=ip)
    user.new_session()
    await user_database.upsert(user)
    return datetime.now()


async def login(request: Request) -> None:
    ip = request.client.host
    await execute_login(ip)


@app.get("/", tags=["Root"])
def root():
    return {"message": "Hello World"}


@app.get("/tickers/", tags=["Tickers"])
async def all_tickers(
    db: TickersDatabase = Depends(_services.get_db),
    _ = Depends(login)
):
    tickers = await _services.get_tickers(db=db)
    response = {}
    for ticker in tickers:
        if ticker.name not in IGNORE_TICKERS:
            response[ticker.id] = ticker.name
    return response


@app.get("/tickers/{ticker_id}", tags=["Tickers"], response_model=_schemas.Ticker)
async def tickers(
    ticker_id: int,
    period: _schemas.PeriodBase = _schemas.PeriodBase.ALL,
    db: TickersDatabase = Depends(_services.get_db),
    _ = Depends(login)
):
    period = _schemas.Period(period=period)  # Convert to Period object
    db_ticker = await _services.get_ticker(db=db, id=ticker_id)
    if db_ticker is None:
        raise HTTPException(
            status_code=404, detail="This Ticker does not exist."
        )
    from_date = datetime.now() - period.delta()
    for fund in db_ticker.funds.keys():
        for i in range(len(db_ticker.funds[fund]["dates"])):
            fund_date = datetime.strptime(db_ticker.funds[fund]["dates"][i], DATE_FORMAT)
            if fund_date >= from_date:
                db_ticker.funds[fund]["dates"] = db_ticker.funds[fund]["dates"][i:]
                db_ticker.funds[fund]["qty"] = db_ticker.funds[fund]["qty"][i:]
                db_ticker.funds[fund]["prices"] = db_ticker.funds[fund]["prices"][i:]
                break
    return db_ticker

# @app.get("/excel/{ticker_id}", tags=["Tickers"], response_class=FileResponse)
# async def excel(
#     ticker_id: int,
#     db: TickersDatabase = Depends(_services.get_db),
#     _ = Depends(login)
# ):
#     db_ticker = await tickers(ticker_id=ticker_id, db=db)
#     some_file_path = ExcelHandler.get_excel(db_ticker.name)
#     return FileResponse(some_file_path, filename=f"{db_ticker.name}.xlsx")

@app.get("/point/{ticker_id}/{date}", tags=["Tickers"], response_model=Dict)
async def point(
    ticker_id: int,
    date: str,
    db: TickersDatabase = Depends(_services.get_db),
    _ = Depends(login)
):
    db_ticker = await tickers(ticker_id=ticker_id, db=db)
    resp = {"date": date, "price": 0.0, "name": db_ticker.name, "funds": []}

    # Add total and avg at the beginning of the table
    first_keys = ["total", "avg"]
    for key in first_keys:
        ind: int = db_ticker.funds[key]["dates"].index(date)
        resp["funds"].append([key, round(db_ticker.funds[key]["qty"][ind], 2)])
        if resp["price"] == 0.0:
            resp["price"] =  round(db_ticker.funds[key]["prices"][ind], 2)
        db_ticker.funds.pop(key)

    for fund in db_ticker.funds.keys():
        try:
            ind: int = db_ticker.funds[fund]["dates"].index(date)
            resp["funds"].append([fund, round(db_ticker.funds[fund]["qty"][ind], 2)])
            if resp["price"] == 0.0:
                resp["price"] =  round(db_ticker.funds[fund]["prices"][ind], 2)
            
        except Exception as e:
            print(f"[WARNING] /point fund name: {fund} error: {str(e)}")
            pass

    return resp

@app.get("/compare/{ticker_id}/{date1}/{date2}", tags=["Tickers"], response_model=Dict)
async def compare(
    ticker_id: int,
    date1: str,
    date2: str,
    db: TickersDatabase = Depends(_services.get_db),
    _ = Depends(login)
):
    resp1: dict = await point(ticker_id=ticker_id, date=date1,db=db)
    resp2: dict = await point(ticker_id=ticker_id, date=date2,db=db)

    dif = {
        "date":date1 + " - " + date2,
        "price":resp2["price"],
        "name":resp2["name"],
        "table":[]
        }
    
    dif["table"].append(["Fund", date1, date2, "Qty Delta", "% Delta"])

   
    # Convert funds to dicts
    resp1_funds_dict: dict = {}
    for fund in resp1["funds"]:
        resp1_funds_dict[fund[0]] = fund[1]
    
    resp2_funds_dict: dict = {}
    for fund in resp2["funds"]:
        resp2_funds_dict[fund[0]] = fund[1]


    # merge the into list without repeating
    keys = list(set(resp1_funds_dict.keys()) | set(resp2_funds_dict.keys()))
    # move the key total and avg to the beginning
    keys.remove("total")
    keys.remove("avg")
    keys = ["total", "avg"] + keys

    for key in keys:

        qty1: float = 0.0
        qty2: float = 0.0
        if key in resp1_funds_dict:
            qty1= resp1_funds_dict[key]
        if key in resp2_funds_dict:
            qty2 = resp2_funds_dict[key]
        
        dif_qty: float = round(qty2 - qty1,2)
        try:
            dif_per: float = round((dif_qty*100)/qty1,2)
        except:
            dif_per: float = 0
        dif["table"].append([key, qty1, qty2, dif_qty, dif_per])

    return dif

@app.get("/hots", tags=["Metrics"])
async def get_hots(
    db: TickersDatabase = Depends(_services.get_db),
    limit: int = 5,
    _ = Depends(login)
) -> List[_schemas.HotColdItem]:
    return await hot_colds_metric.get_hots(db=db, limit=limit, ignore=IGNORE_TICKERS)

@app.get("/colds", tags=["Metrics"])
async def get_colds(
    db: TickersDatabase = Depends(_services.get_db),
    limit: int = 5,
    _ = Depends(login)
) -> List[_schemas.HotColdItem]:
    return await hot_colds_metric.get_colds(db=db, limit=limit, ignore=IGNORE_TICKERS)

@app.post("/support_ticket", tags=["Support"])
async def support_ticket(msg: str):
    with open("support.txt", "a") as f:
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"{now} - {msg}")

@app.get("/users/{password}", tags=["Support"])
async def users(password: str) -> List[_schemas.User]:
    if password != ENGINE_PSWD:
        raise HTTPException(status_code=403, detail="Incorrect password")
    
    user_database = UsersDatabase()
    users = await user_database.get_all()
    return users

@app.get("/support_ticket/{password}", tags=["Support"])
async def support_ticket(password: str):
    if password != ENGINE_PSWD:
        return "Wrong password"
    
    with open("support.txt", "r") as f:
        return f.read()

# @app.post("/engineUpdate/{password}/{today}", tags=["Engine"])
# async def update_engine(password: str,today: str, request: Request, db: TickersDatabase = Depends(_services.get_db)):
#     try:
#         if password == ENGINE_PSWD:
#             payload = await request.json()
#             ExcelHandler.update_excel(payload, today)
#             for t in payload.keys():
#                 db_ticker = await _services.get_ticker_by_name(db=db, name=t)
#                 if db_ticker:
#                     new_fund: dict = db_ticker.funds
#                     for f in payload[t].keys():
#                         if f in new_fund.keys():
#                             if today != new_fund[f]["dates"][-1]:
#                                 new_fund[f]["dates"].append(today)
#                                 new_fund[f]["qty"].append(payload[t][f]["qty"])
#                                 new_fund[f]["prices"].append(payload[t][f]["price"])
#                             else:
#                                 new_fund[f]["qty"][-1] = payload[t][f]["qty"]
#                                 new_fund[f]["prices"][-1] = payload[t][f]["price"]
#                         else:
#                             new_fund[f] = {"dates": [today], "qty": [payload[t][f]["qty"]], "prices": [payload[t][f]["price"]]}
#                     await _services.update_ticker(db=db, ticker=_schemas.createTicker(name=t,funds=new_fund,price=0,type="basic"))                
#                 else:
#                     new_fund: dict = {}
#                     for f in payload[t].keys():
#                         new_fund[f] = {"dates": [today], "qty": [payload[t][f]["qty"]], "prices": [payload[t][f]["price"]]}
#                     await _services.create_ticker(db=db, ticker=_schemas.Ticker(name=t,funds=new_fund,price=0,type="basic"))
#         else:
#             return "Incorrect Password"
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         print("[ERROR] engineUpdate: ",e)
#         raise HTTPException(
#                 status_code=500, detail=f"Internal Server Error {exc_type} {exc_tb.tb_lineno} {e}"
#             )    

@app.post("/delete/{password}/{name}", tags=["Engine"])
async def delete_ticker(password: str, name: str, db: TickersDatabase = Depends(_services.get_db)):
    try:
        if password == ENGINE_PSWD:
            await _services.delete_ticker_by_name(db, name)
        else:
            return "Incorrect Password"
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("[ERROR] engineUpdate: ",e)
        raise HTTPException(
                status_code=500, detail=f"Internal Server Error {exc_type} {exc_tb.tb_lineno} {e}"
            )
# -------------------------------------------------------------------
# PLAYGROUND
# -------------------------------------------------------------------
@app.get("/test")
async def test(db: TickersDatabase = Depends(_services.get_db)):
    tickers = await _services.get_tickers(db=db)
    user_database = TickersDatabase()
    for ticker in tickers:
        ticker = _schemas.Ticker(
            id=ticker.id,
            name=ticker.name,
            funds=ticker.funds,
            price=ticker.price,
            type=ticker.type
        )
        await user_database.create(ticker)

    
    
# -------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio")