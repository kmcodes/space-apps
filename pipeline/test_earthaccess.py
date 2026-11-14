import earthaccess

earthaccess.login(persist=True)
r = earthaccess.search_data(
    short_name="SPL3SMP_E",
    bounding_box=(76, 20, 77.5, 21),
    temporal=("2025-10-01", "2025-10-07"),
)
print(len(r))
