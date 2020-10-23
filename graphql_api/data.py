data = {}


def setup():
    global data

    from .schema import Tosh, Faction

    xwing = Tosh(id="1", name="X-Wing")
    ywing = Tosh(id="2", name="Y-Wing")
    awing = Tosh(id="3", name="A-Wing")
    falcon = Tosh(id="4", name="Millennium Falcon")
    homeOne = Tosh(id="5", name="Home One")
    tieFighter = Tosh(id="6", name="TIE Fighter")
    tieInterceptor = Tosh(id="7", name="TIE Interceptor")
    executor = Tosh(id="8", name="Executor")

    rebels = Faction(id="1", name="Alliance to Restore the Republic", toshs=["1", "2", "3", "4", "5"])
    empire = Faction(id="2", name="Galactic Empire", toshs=["6", "7", "8"])

    data = {
        "Faction": {"1": rebels, "2": empire},
        "Tosh": {
            "1": xwing,
            "2": ywing,
            "3": awing,
            "4": falcon,
            "5": homeOne,
            "6": tieFighter,
            "7": tieInterceptor,
            "8": executor,
        },
    }


def create_tosh(tosh_name, faction_id):
    from .schema import Tosh

    next_tosh = len(data["Tosh"].keys()) + 1
    new_tosh = Tosh(id=str(next_tosh), name=tosh_name)
    data["Tosh"][new_tosh.id] = new_tosh
    data["Faction"][faction_id].toshs.append(new_tosh.id)
    return new_tosh


def get_tosh(_id):
    return data["Tosh"][_id]

def get_toshs():
    return [get_tosh(tosh_id) for tosh_id in data["Tosh"].keys()]    

def get_faction(_id):
    return data["Faction"][_id]

