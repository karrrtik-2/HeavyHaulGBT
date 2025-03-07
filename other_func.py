# GENERAL FUNCTIONS
def fetch_order_id(data):
    return data.get("id", "Key not found")

def fetch_order_status(data):
    return data.get("order_status", "Key not found")

def fetch_estimated_cost_value(data):
    return data.get("order", {}).get("estimatedTotalCostValue", "Key not found")

def fetch_trailor_type(data):
    return data.get("order", {}).get("Trailer_Type", "Key not found")


# handling should be diff for thes ebelow functions

def fetch_pickup_address(data):
    return data.get("order", {}).get("pickupFormattedAddress", "Key not found")

def fetch_overall_route(data):
    return data.get("order", {}).get("order_comment_map_link", "Key not found")

def fetch_invoice(data):
    return data.get("order", {}).get("invoice_url", "Key not found")

def fetch_delivery_address(data):
    return data.get("order", {}).get("deliveryFormatedAddress", "Key not found")

def fetch_delivery_address(data):
    return data.get("order", {}).get("deliveryFormatedAddress", "Key not found")

def fetch_delivery_address(data):
    return data.get("order", {}).get("deliveryFormatedAddress", "Key not found")

def fetch_order_created_date(data):
    return data.get("order_created_date", "Key not found")

def fetch_permitcount(data):
    return data.get("order", {}).get("permitcount", "Key not found")

def fetch_total_paid_amount(data):
    return data.get("order", {}).get("totalPaidAmount", "Key not found")

def fetch_total_due(data):
    return data.get("order", {}).get("total_due", "Key not found")

def fetch_onlyForRouteIdeas(data):
    return data.get("order", {}).get("onlyForRouteIdeas",{})

def fetch_transactions(data):
    return data.get("order", {}).get("transactions", [])

def fetch_token(data):
    return data.get("token", "Key not found")

def fetch_totalWeight(data):
    return data.get("order", {}).get("totalWeight", "Weight not found")


# FUNCTIONS FOR AXLE SPACING AND WEIGHT
def fetch_axle_spacing(data):
    axle_spacing_list = data.get("order", {}).get("axle_spacing", [])
    axle_spacing_dict = {item["name"]: item["value"] for item in axle_spacing_list}
    return axle_spacing_dict if axle_spacing_dict else "Key not found"

def fetch_axle_weight(data):
    axle_weight_list = data.get("order", {}).get("axle_weight", [])
    axle_weight_dict = {item["name"]: item["value"] for item in axle_weight_list}
    return axle_weight_dict if axle_weight_dict else "Key not found"

# FUNCTIONS FOR CLIENT
def fetch_client_id(data):
    return data.get("client_id", "Key not found")

def fetch_client_name(data):
    return data.get("order", {}).get("clientData", {}).get("name", "Key not found") + " " + data.get("order", {}).get("clientData", {}).get("last_name", "Key not found")

def fetch_client_phone(data):
    return data.get("order", {}).get("clientData", {}).get("phone", "Key not found")

def fetch_client_email(data):
    return data.get("order", {}).get("clientData", {}).get("email", "Key not found")


# FUNCTIONS FOR DRIVER
def fetch_driver_id(data):
    return data.get("driver_id", "Key not found")

def fetch_driver_name(data):
    return data.get("order", {}).get("driverData", {}).get("name", "Key not found") + " " + data.get("order", {}).get("driverData", {}).get("last_name", "Key not found")

def fetch_driver_phone(data):
    return data.get("order", {}).get("driverData", {}).get("phone", "Key not found")

def fetch_driver_email(data):
    return data.get("order", {}).get("driverData", {}).get("email", "Key not found")

# FUNCTIONS FOR TRUCK
def fetch_truck_id(data):
    return data.get("order", {}).get("truck_detail",{}).get("unit_id", "Key not found")

def fetch_truck_detail(data):
    return data.get("order", {}).get("truck_detail",{}).get("truck_detail", "Key not found")

def fetch_truck_make(data):
    return data.get("order", {}).get("truck_detail",{}).get("make", "Key not found")

def fetch_truck_model(data):
    return data.get("order", {}).get("truck_detail",{}).get("model", "Key not found")

def fetch_truck_vin(data):
    return data.get("order", {}).get("truck_detail",{}).get("vin", "Key not found")

def fetch_truck_license_plate(data):
    return data.get("order", {}).get("truck_detail",{}).get("license_plate", "Key not found")

def fetch_truck_license_state(data):
    return data.get("order", {}).get("truck_detail",{}).get("license_state", "Key not found")

def fetch_truck_axle(data):
    return data.get("order", {}).get("truck_detail",{}).get("axle", "Key not found")

def fetch_carrier_name(data):
    return data.get("order", {}).get("truck_detail",{}).get("carrier_name", "Key not found")

def fetch_carrier_dot(data):
    return data.get("order", {}).get("truck_detail",{}).get("carrier_dot", "Key not found")

def fetch_truck_year(data):
    return data.get("order", {}).get("truck_detail",{}).get("year", "year not found")

def fetch_license_state(data):
    return data.get("order", {}).get("truck_detail",{}).get("license_state", "Key not found")

def fetch_truck_registration(data):
    return data.get("order", {}).get("truck_detail",{}).get("registration", "link not found")

def fetch_truck_reg_exp(data):
    return data.get("order", {}).get("truck_detail",{}).get("registration_exp", "reg exp date not found")

# FUNCTIONS FOR TRAILER
def fetch_trailer_id(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("trailer_id", "Key not found")

def fetch_trailer_model(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("model", "Key not found")

def fetch_trailer_year(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("year", "Key not found")

def fetch_trailer_vin(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("vin", "Key not found")

def fetch_trailer_license_plate(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("license_plate", "Key not found")

def fetch_state(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("state", "Key not found")

def fetch_trailer_length(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("length", "Key not found")

def fetch_trailer_type(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("type", "Key not found")

def fetch_trailer_make(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("make", "Key not found")

def fetch_trailer_axle(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("axle", "Key not found")

def fetch_king_pin(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("king_pin", "Key not found")

def fetch_kin_pin_in(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("kin_pin_in", "Key not found")

def fetch_trailer_axle_type(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("axle_type", "Key not found")

def fetch_empty_weight(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("empty_weight", "Key not found")

def fetch_trailer_registration(data):
    return data.get("order", {}).get("Trailer_Info",{}).get("registration", "link not found") + " , " + data.get("order", {}).get("Trailer_Info",{}).get("registration_exp", "reg exp date not found")
    
# FUNCTIONS FOR OVERALL DATA AND DIMENSIONS
def fetch_OverallOrderData(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("empty_weight", "Key not found")

def fetch_overalltrucktrailer(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("overalltrucktrailer", "Key not found")

def fetch_overalllength(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("overalllength", "Key not found")

def fetch_overallwidth(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("overallwidth", "Key not found")

def fetch_overallheight(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("overallheight", "Key not found")

def fetch_overallweight(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("overallweight", "Key not found")

def fetch_front_overhang(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("front_overhang", "Key not found")

def fetch_rear_overhang(data):
    return data.get("order", {}).get("OverallOrderData",{}).get("rear_overhang", "Key not found")


# FUNCTIONS FOR STATE
def fetch_state_name(data):
    route_data = data.get("order", {}).get("routeData", [])
    result = []
    
    for item in route_data:
        if item.get("permit_status") != "Delete":
            state_name = item.get("state_name", "Key not found")
            start_date = item.get("start_date", "Date not found")
            result.append(f"{state_name} - {start_date}")
    
    return result

def fetch_permit_status(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("permit_status", "Key not found") for item in route_data if item.get("permit_status") != "Delete"]

def fetch_permit_info(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("permit_info", "Permit not found") for item in route_data if item.get("permit_status") != "Delete"]

# state fee is permit fee and other fee is state fee ,
# and total price = (permit fee + state fee + service fee) and Price key is wrong in orders i dont know on which basis it is calculated

def fetch_state_fee(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("state_fee", "Key not found") for item in route_data if item.get("permit_status") != "Delete"]

def fetch_price(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("price", "Key not found") for item in route_data if item.get("permit_status") != "Delete"]

def fetch_other_fee(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("other_fee", "Key not found") for item in route_data if item.get("permit_status") != "Delete"]

def fetch_service_fee(data):
    route_data = data.get("order", {}).get("routeData", [])
    return [item.get("service_fee", "Key not found") for item in route_data if item.get("permit_status") != "Delete"]

#update this to fetch all the route urls for the req state
def fetch_route_url(data):
    route_data = data.get("order", {}).get("routeData", [])
    
    return [
        {
            f"route_url_{i}": item.get(f"route_url_{i}", "Key not found")
            for i in range(1, 4)  # Assuming route_url_1 to route_url_3
            if item.get(f"route_url_status_{i}") == "Approved"
        }
        for item in route_data
    ]

# FUNCTIONS FOR COMMODITY
def fetch_commodityDataAndDimension(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("trailer_length", "Key not found")

def fetch_pickup_date(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("pickup_date", "Key not found")

def fetch_length(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("length", "Key not found")

def fetch_width(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("width", "Key not found")

def fetch_height(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("height", "Key not found")

def fetch_weight(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("weight", "Key not found")

def fetch_make(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("make", "Key not found")

def fetch_model(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("model", "Key not found")

def fetch_description(data):
    return data.get("order", {}).get("commodityDataValue",{}).get("description", "Key not found")
