# pyCode/move_drone.py
# 사용: python3 -u pyCode/move_drone.py <x1> <y1> <z1> <x2> <y2> <z2> ...
import asyncio
import sys
from typing import List, Tuple
from mavsdk import System

# === 설정 ===
TAKEOFF_ALT_M = 5.0        # 5m 이륙
WP_HOLD_SEC   = 15          # 각 웨이포인트에서 유지 시간 (10~15 중 골라서 쓰면 됨)

def parse_coords(argv: List[str]) -> List[Tuple[float,float,float]]:
    if len(argv) % 3 != 0:
        print(f"[ERR] args must be multiples of 3, got {len(argv)}")
        sys.exit(2)
    coords = []
    for i in range(0, len(argv), 3):
        lat = float(argv[i]); lon = float(argv[i+1]); z = float(argv[i+2])
        coords.append((lat, lon, z))
    return coords

async def wait_connected(drone: System):
    print("-- Waiting connection")
    async for s in drone.core.connection_state():
        if s.is_connected:
            print("-- Connected")
            break

async def wait_global_ready(drone: System):
    print("-- Waiting for global position estimate")
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            print("-- Global position OK")
            break

async def get_home_abs_alt(drone: System) -> float:
    async for home in drone.telemetry.home():
        return home.absolute_altitude_m

async def wait_until_landed(drone: System):
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("-- Landed")
            break
        await asyncio.sleep(0.5)

async def main():
    coords = parse_coords(sys.argv[1:])
    if not coords:
        print("[ERR] no coordinates provided")
        return

    drone = System()
    await drone.connect(system_address="udp://:14540")

    await wait_connected(drone)
    await wait_global_ready(drone)

    # 1) Arm
    print("-- Arming")
    await drone.action.arm()

    # 2) Takeoff to 5m (AMSL 계산 위해 home AMSL에 상대 5m를 더해 사용)
    home_amsl = await get_home_abs_alt(drone)
    target_amsl = home_amsl + TAKEOFF_ALT_M
    print(f"-- Taking off to ~{TAKEOFF_ALT_M} m AGL (AMSL≈{target_amsl:.2f})")
    await drone.action.takeoff()
    await asyncio.sleep(8)  # 모터/상승 안정화 텀

    # 3) Waypoint 이동 (각 포인트당 WP_HOLD_SEC 유지)
    print(f"-- Moving through {len(coords)} waypoints, hold {WP_HOLD_SEC}s each")
    for idx, (lat, lon, _z_db) in enumerate(coords, start=1):
        # 저장 z는 무시하고, 일정 고도(5m AGL)로 이동
        print(f"--- WP {idx}/{len(coords)}: goto lat={lat}, lon={lon}, amsl={target_amsl:.2f}")
        await drone.action.goto_location(lat, lon, target_amsl, 0.0)
        await asyncio.sleep(WP_HOLD_SEC)

    # 4) 착륙
    print("-- Landing")
    await drone.action.land()
    await wait_until_landed(drone)

    print("-- Disarming")
    await drone.action.disarm()

    print("== DONE ==")

if __name__ == "__main__":
    asyncio.run(main())
