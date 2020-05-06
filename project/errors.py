class CityError(Exception):

    pass


class DepartureCityError(CityError):

    pass


class ArivalCityError(CityError):

    pass


class CityNotFound(CityError):

    pass


class FlightNumberError(Exception):

    pass