"""buff api"""
import requests
import json
import pickle
import os
import sqlite3

class Goods:
    def __init__(self, goods_id, cost=0):
        self.index = 0
        self.id = goods_id  # buff id
        self.youpin_id = 0

        self.name = ''  # name
        self.cost = cost  # 购入花费
        self.price = 0  # buff当前价格
        self.steam_price = 0  # steam当前价格

        self.status = 0  # 0:在库中 1:租出 2:卖出

        self.on_sale_count = 0  # youpin在售
        self.on_lease_count = 0  # youpin租出
        self.lease_unit_price = 0  # youpin短租金
        self.long_lease_unit_price = 0  # youpin长租金
        self.youpin_price = 0  # youpin当前价格
        self.deposit = 0  # 押金
        self.sell_price = 0  # 卖出价格
        self.__get_buff()
        self.__get_youpin()

    def __get_buff(self):
        url = (
            'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id='
            + self.id
        )
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            self.price = eval(data['data']['items'][0]['price'])
            self.name = data['data']['goods_infos'][self.id]['name']
            self.steam_price = eval(
                data['data']['goods_infos'][self.id]['steam_price_cny']
            )
            return True
        else:
            return False

    def __get_youpin(self):
        # self.name -> youpin_id
        conn = sqlite3.connect('./crawler/youpinDB.db')
        cursor = conn.cursor()
        cursor.execute("SELECT Id FROM youpinItem WHERE CommodityName=?", (self.name,))
        result = cursor.fetchone()
        #print(result)
        url = "https://api.youpin898.com/api/homepage/es/commodity/GetCsGoPagedList"

        payload = json.dumps({
        "hasSold": "true",
        "haveBuZhangType": 0,
        "listSortType": "1",
        "listType": 10,
        "pageIndex": 1,
        "pageSize": 50,
        "sortType": "1",
        "status": "20",
        "stickersIsSort": False,
        "templateId": f"{result[0]}",
        "userId": ""
        })
        headers = {
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()
        #print(response)
        self.youpin_id = result
        self.on_sale_count = 1 # response['Data']['CommodityList'][0]["OnSaleCount"]  # youpin在售
        self.on_lease_count = 1 #response['Data']['CommodityList'][0]["OnLeaseCount"]  # youpin租出
        self.lease_unit_price =1 #eval(response['Data']['CommodityList'][0]["LeaseUnitPrice"])  # youpin短租金
        self.long_lease_unit_price = 1 #eval(
        #    response['Data']['CommodityList'][0]["LongLeaseUnitPrice"]
        #)  # youpin长租金
        self.youpin_price = eval(response['Data']['CommodityList'][0]["Price"])  # youpin当前价格
        self.deposit = 1 #eval(response['Data']['CommodityList'][0]["LeaseDeposit"])  # 押金

    def refresh(self):
        self.__get_buff()
        self.__get_youpin()

    def sell(self, price):
        self.status = 2
        self.sell_price = price

    def lease(self):
        self.status = 1

    def back(self):
        self.status = 0

    def get_status(self):
        if self.status == 0 and self.cost != 0:
            return "在库中"
        elif self.status == 1:
            return "租出"
        elif self.status == 0 and self.cost == 0:
            return "观望中"
        else:
            return "卖出"

    def __call__(self):
        if self.cost == 0:
            return {
                "BuffId": self.id,
                "YoupinId": self.youpin_id,
                "Name": self.name,
                "Cost": self.cost,
                "BuffPrice": self.price,
                "YoupinPrice": self.youpin_price,
                "SteamPrice": self.steam_price,
                "Status": self.status,
                "OnSaleCount": self.on_sale_count,
                "OnLeaseCount": self.on_lease_count,
                "LeaseUnitPrice": self.lease_unit_price,
                "LongLeaseUnitPrice": self.long_lease_unit_price,
                "Deposit": self.deposit,
                "RentSaleRatio": self.on_lease_count / self.on_sale_count,  # 目前租售比
                "LeaseRatio": self.lease_unit_price / self.price * 100,  # 租金比例
                "DepositRatio": self.deposit / self.price * 100,  # 押金比例
                "AnnualizedShortTermLeaseRatio": 192
                * self.lease_unit_price
                / self.price
                * 100,  # 年化短租比例
                "AnnualizedLongTermLeaseRatio": 264
                * self.long_lease_unit_price
                / self.price
                * 100,  # 年化长租比例
                "CashRatio": self.price / self.steam_price * 100,  # 套现比例
                "BuffYouyouRatio": self.price / self.youpin_price,  # buff和有品价格比例
            }
        else:
            return {
                "BuffId": self.id,
                "YoupinId": self.youpin_id,
                "Name": self.name,
                "Cost": self.cost,
                "BuffPrice": self.price,
                "YoupinPrice": self.youpin_price,
                "SteamPrice": self.steam_price,
                "Status": self.status,
                "OnSaleCount": self.on_sale_count,
                "OnLeaseCount": self.on_lease_count,
                "LeaseUnitPrice": self.lease_unit_price,
                "LongLeaseUnitPrice": self.long_lease_unit_price,
                "Deposit": self.deposit,
                "RentSaleRatio": self.on_lease_count / self.on_sale_count,  # 目前租售比
                "TheoreticalCurrentEarnings": self.youpin_price*0.99 - self.cost,  # 理论目前收益（有品）
                "TheoreticalCurrentEarningsRate": (self.youpin_price*0.99 - self.cost)
                / self.cost
                * 100 if self.cost !=0 else 0,  # 理论目前收益率（有品）
                "BuffCurrentEarnings": self.price*0.975*0.99 - self.cost,  # Buff当前收益
                "BuffCurrentEarningsRate": (self.price*0.975*0.99 - self.cost)
                / self.cost
                * 100 if self.cost !=0 else 0,  # 理论目前收益率（Buff）
                "LeaseRatio": self.lease_unit_price / self.price * 100,  # 租金比例
                "DepositRatio": self.deposit / self.price * 100,  # 押金比例
                "AnnualizedShortTermLeaseRatio": 192
                * self.lease_unit_price
                / self.price
                * 100,  # 年化短租比例
                "AnnualizedLongTermLeaseRatio": 264
                * self.long_lease_unit_price
                / self.price
                * 100,  # 年化长租比例
                "CashRatio": self.price / self.steam_price * 100,  # 套现比例
                "BuffYouyouRatio": self.price / self.youpin_price,  # buff和有品价格比例
            }


class Inventory:
    """库存管理"""
    
    def __init__(self, path) -> None:
        """选择一个库存并启动该库存"""
        self.path = path
        self.index_counter = 0  # 自增计数器
        self.__data = {}
        
        if os.path.exists(path):
            saved_data = pickle.load(open(path, "rb"))
            # 加载已保存的数据和计数器
            if isinstance(saved_data, tuple) and len(saved_data) == 2:
                self.__data = saved_data[0]
                self.index_counter = saved_data[1]
            else:  # 兼容旧版本数据格式
                self.__data = saved_data
                if self.__data:
                    self.index_counter = max(int(k) for k in self.__data.keys()) + 1

    def __call__(self):
        return self.__data

    def __iter__(self):
        return self.__data.__iter__()

    def add(self, good: Goods):
        if good.__class__ == Goods:
            good.index = self.index_counter  # 使用自增计数器
            self.__data[good.index] = good
            self.index_counter += 1  # 计数器递增
        else:
            raise TypeError("输入类型错误")

    def delete(self, good):
        del self()[good]

    def save(self):
        pickle.dump(self.__data, open(self.path, "wb"))

    def reset(self):
        self.__data = []

    def total_cost(self):
        return sum([self()[good].cost for good in self()])

    def total_cost_in_inventory(self):
        return sum(
            [
                self()[good].cost
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def calc_buff_earn(self):
        return sum(
            [
                self()[good].price*0.975*0.99 - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 and self()[good].status == 0) or self()[good].status == 1
            ]
        )

    def calc_youpin_earn(self):
        return sum(
            [
                self()[good].youpin_price*0.99 - self()[good].cost  # 仅扣除1%手续费
                for good in self()
                if (self()[good].cost != 0 and self()[good].status == 0) or self()[good].status == 1
            ]
        )

    def calc_buff_earn_rate(self):
        return self.calc_buff_earn() / self.total_cost_in_inventory() * 100

    def calc_youpin_earn_rate(self):
        return self.calc_youpin_earn() / self.total_cost_in_inventory() * 100

    def calc_buff_earn_rate(self):
        return self.calc_buff_earn() / self.total_cost_in_inventory() * 100

    def calc_youpin_earn_rate(self):
        return self.calc_youpin_earn() / self.total_cost_in_inventory() * 100

    def calc_price(self):
        return sum(
            [
                self()[good].price
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def calc_yyyp_price(self):
        return sum(
            [
                self()[good].youpin_price
                for good in self()
                if (self()[good].status == 0 and self()[good].cost != 0)
                or self()[good].status == 1
            ]
        )

    def sell_earn(self):
        return sum(
            [self()[good].sell_price for good in self() if self()[good].status == 2]
        ) - sum(
            [self()[good].cost for good in self() if self()[good].status == 2]
        )

    def sell_price(self):
        return sum(
            [self()[good].sell_price for good in self() if self()[good].status == 2]
        )

    def calc_buff_earn(self):
        return sum(
            [
                self()[good].price*0.975*0.99 - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 and self()[good].status == 0) or self()[good].status == 1
            ]
        )

    def calc_youpin_earn(self):
        return sum(
            [
                self()[good].youpin_price*0.99 - self()[good].cost
                for good in self()
                if (self()[good].cost != 0 and self()[good].status == 0) or self()[good].status == 1
            ]
        )


if __name__ == "__main__":
    g = Goods('759220', 22.5)
    print(g)
