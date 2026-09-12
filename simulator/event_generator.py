"""
High-throughput pharmaceutical supply chain event simulator.
Generates inventory stock events (with seasonal demand and shortage shocks)
and IoT shipment cold-chain telemetry events.
"""

import argparse
import json
import logging
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulator.disruption_injector import DisruptionInjector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STAGED_DIR = Path("data-ingestion/staged")
OUTPUT_DIR = Path("simulator/generated")


class PharmaSupplyChainSimulator:
    def __init__(
        self,
        num_pharmacies: int = 300,
        num_drugs: int = 150,
        sim_days: int = 30,
        time_dilation: float = 1.0,  # 1 simulated day per time_dilation seconds
        random_seed: int = 42
    ):
        self.num_pharmacies = num_pharmacies
        self.num_drugs = num_drugs
        self.sim_days = sim_days
        self.time_dilation = time_dilation
        self.random_seed = random_seed
        self.start_date = datetime(2024, 1, 1, 8, 0, 0)

        random.seed(random_seed)
        self.disruption_injector = DisruptionInjector()
        self._load_entities()

    def _load_entities(self):
        """Loads and selects reduced representative subsets of pharmacies, drugs, and topology."""
        with open(STAGED_DIR / "pharmacies.json", "r", encoding="utf-8") as f:
            all_pharmacies = json.load(f)
        with open(STAGED_DIR / "drugs.json", "r", encoding="utf-8") as f:
            all_drugs = json.load(f)
        with open(STAGED_DIR / "manufacturers.json", "r", encoding="utf-8") as f:
            self.manufacturers = json.load(f)
        with open(STAGED_DIR / "topology_edges.json", "r", encoding="utf-8") as f:
            self.topology = json.load(f)

        # Methodology Choice: Sample representative subsets
        self.pharmacies = all_pharmacies[:min(self.num_pharmacies, len(all_pharmacies))]
        self.drugs = all_drugs[:min(self.num_drugs, len(all_drugs))]
        self.distributors = self.topology.get("distributor_nodes", [])

        # Initialize inventory states for each (pharmacy, drug)
        self.inventory_state = {}
        for p in self.pharmacies:
            p_id = p["pharmacy_id"]
            self.inventory_state[p_id] = {}
            for d in self.drugs:
                d_id = d["drug_id"]
                # Base stock between 50 and 300 units
                base_stock = random.randint(60, 250)
                base_daily_demand = random.randint(8, 28)
                self.inventory_state[p_id][d_id] = {
                    "current_stock": base_stock,
                    "base_demand": base_daily_demand,
                    "reorder_point": base_daily_demand * 4,
                    "target_stock": base_daily_demand * 12,
                    "pending_order_units": 0,
                    "last_order_day": -10
                }

        logger.info(
            f"Simulator initialized: {len(self.pharmacies)} pharmacies × {len(self.drugs)} drugs "
            f"({len(self.pharmacies) * len(self.drugs):,} inventory pairings), {self.sim_days} simulated days."
        )

    def calculate_seasonal_demand(self, base_demand: float, day_offset: int, is_biologic: bool) -> int:
        """Computes daily demand with sinusoidal annual seasonality + weekly fluctuations + noise."""
        # 365-day annual cycle
        annual_cycle = math.sin(2 * math.pi * (day_offset % 365) / 365.0)
        seasonal_multiplier = 1.0 + (0.35 * annual_cycle if is_biologic else 0.20 * annual_cycle)

        # Day of week factor (higher on Mon/Tue, lower on weekends)
        dow = day_offset % 7
        dow_factor = 1.15 if dow in [1, 2] else (0.80 if dow in [5, 6] else 1.0)

        noise = random.gauss(1.0, 0.12)
        demand = max(1, int(round(base_demand * seasonal_multiplier * dow_factor * noise)))
        return demand

    def generate_day_events(self, day_offset: int):
        """Simulates one complete 24-hour cycle of stock movements and shipment telemetry."""
        current_sim_time = self.start_date + timedelta(days=day_offset)
        year_month = current_sim_time.strftime("%Y-%m")
        timestamp_str = current_sim_time.isoformat()

        stock_events = []
        shipment_events = []

        # 1. Simulate Inventory & Consumption across Pharmacies
        for p in self.pharmacies:
            p_id = p["pharmacy_id"]
            for d in self.drugs:
                d_id = d["drug_id"]
                inv = self.inventory_state[p_id][d_id]
                is_biologic = d.get("is_biologic", False)

                # Check for active FDA calibrated disruption
                disruption = self.disruption_injector.get_disruption_impact(d_id, day_offset)
                demand = self.calculate_seasonal_demand(inv["base_demand"], day_offset, is_biologic)

                # Consume stock
                inv["current_stock"] = max(0, inv["current_stock"] - demand)
                stockout = (inv["current_stock"] == 0)

                # Restock Triggering
                restock_order_id = None
                if inv["current_stock"] <= inv["reorder_point"] and (day_offset - inv["last_order_day"]) >= 3:
                    order_qty = inv["target_stock"] - inv["current_stock"]
                    
                    # If disruption active, drastically suppress order fulfillment
                    if disruption["is_disrupted"]:
                        order_qty = int(order_qty * disruption["supply_multiplier"])
                    
                    if order_qty > 0:
                        restock_order_id = f"ORD-{day_offset:03d}-{p_id[-4:]}-{d_id[-4:]}"
                        inv["pending_order_units"] = order_qty
                        inv["last_order_day"] = day_offset

                # Restock Arrival (simulate lead time: 2 days normal, lengthened during disruptions)
                lead_time = 2
                if disruption["is_disrupted"]:
                    lead_time = int(lead_time * disruption["lead_time_penalty_factor"])

                if inv["pending_order_units"] > 0 and (day_offset - inv["last_order_day"]) >= lead_time:
                    inv["current_stock"] += inv["pending_order_units"]
                    inv["pending_order_units"] = 0

                event = {
                    "event_id": f"STK-{day_offset:03d}-{p_id[-6:]}-{d_id[-6:]}",
                    "event_type": "STOCKOUT" if stockout else "STOCK_UPDATE",
                    "pharmacy_id": p_id,
                    "drug_id": d_id,
                    "current_stock": inv["current_stock"],
                    "daily_demand": demand,
                    "stockout_flag": stockout,
                    "disruption_active": disruption["is_disrupted"],
                    "shortage_id": disruption.get("shortage_id"),
                    "restock_order_id": restock_order_id,
                    "timestamp": timestamp_str,
                    "year_month": year_month
                }
                stock_events.append(event)

        # 2. Simulate Active In-Transit Shipment Telemetry
        # Weight active shipment dispatch by drug supply availability (shortage suppression)
        drug_weights = [
            self.disruption_injector.get_disruption_impact(d["drug_id"], day_offset)["supply_multiplier"]
            for d in self.drugs
        ]
        num_active_shipments = random.randint(30, 70)
        for s_idx in range(num_active_shipments):
            drug = random.choices(self.drugs, weights=drug_weights, k=1)[0]
            d_id = drug["drug_id"]
            mfr_id = drug.get("manufacturer_id", "EST-0001")
            pharmacy = random.choice(self.pharmacies)
            p_id = pharmacy["pharmacy_id"]
            
            storage_cond = drug.get("storage_condition", {})
            requires_cold = drug.get("requires_cold_chain", False)
            min_temp = storage_cond.get("min_temp_celsius", 2.0)
            max_temp = storage_cond.get("max_temp_celsius", 8.0)

            # Normal temperature with occasional thermal excursion (5% probability)
            is_excursion = (random.random() < 0.05) if requires_cold else False
            if is_excursion:
                temp = round(max_temp + random.uniform(2.5, 9.0), 2)  # Excursion above limit
            elif requires_cold:
                temp = round(random.uniform(min_temp + 0.5, max_temp - 0.5), 2)
            else:
                temp = round(random.uniform(18.0, 23.0), 2)

            batch_id = f"BAT-2024-{hash(d_id) % 9000 + 1000:04d}-{s_idx:02d}"
            shipment_id = f"SHP-{day_offset:03d}-{s_idx:03d}"

            # GPS interpolation between manufacturer and pharmacy
            lat = round(float(pharmacy.get("latitude", 34.0)) + random.uniform(-0.5, 0.5), 6)
            lon = round(float(pharmacy.get("longitude", -118.0)) + random.uniform(-0.5, 0.5), 6)

            telemetry_event = {
                "event_id": f"TEL-{day_offset:03d}-{s_idx:04d}",
                "event_type": "EXCURSION_ALERT" if is_excursion else "TELEMETRY_PING",
                "shipment_id": shipment_id,
                "batch_id": batch_id,
                "drug_id": d_id,
                "source_mfr_id": mfr_id,
                "target_node_id": p_id,
                "temperature_celsius": temp,
                "humidity_percent": round(random.uniform(40.0, 65.0), 1),
                "vibration_g": round(random.uniform(0.05, 0.35 if not is_excursion else 1.2), 3),
                "is_excursion": is_excursion,
                "requires_cold_chain": requires_cold,
                "latitude": lat,
                "longitude": lon,
                "status": "IN_TRANSIT",
                "timestamp": timestamp_str,
                "year_month": year_month
            }
            shipment_events.append(telemetry_event)

        return stock_events, shipment_events

    def run_simulation(self, publish_callback=None):
        """Runs multi-day simulation loop, yielding or publishing events."""
        logger.info(f"Beginning simulation run for {self.sim_days} days (dilation: {self.time_dilation}s/day)...")
        total_stock = 0
        total_shipment = 0

        for day in range(self.sim_days):
            t0 = time.time()
            stock_events, shipment_events = self.generate_day_events(day)
            total_stock += len(stock_events)
            total_shipment += len(shipment_events)

            stockouts = sum(1 for s in stock_events if s["stockout_flag"])
            excursions = sum(1 for sh in shipment_events if sh["is_excursion"])

            logger.info(
                f"[Sim Day {day + 1:02d}/{self.sim_days:02d}] Generated {len(stock_events):,} stock events "
                f"({stockouts} stockouts), {len(shipment_events)} shipment telemetry pings ({excursions} excursions)."
            )

            if publish_callback:
                publish_callback(stock_events, shipment_events)

            elapsed = time.time() - t0
            sleep_time = max(0.0, self.time_dilation - elapsed)
            if sleep_time > 0 and self.time_dilation > 0.05:
                time.sleep(sleep_time)

        logger.info(f"Simulation completed: {total_stock:,} total stock events, {total_shipment:,} total shipment events.")
        return total_stock, total_shipment


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pharmaceutical IoT & Supply Chain Simulator")
    parser.add_argument("--days", type=int, default=5, help="Number of simulated days")
    parser.add_argument("--dilation", type=float, default=0.5, help="Seconds per simulated day (accelerated pace)")
    parser.add_argument("--pharmacies", type=int, default=100, help="Number of pharmacies in simulation sample")
    parser.add_argument("--drugs", type=int, default=50, help="Number of drugs in simulation sample")
    parser.add_argument("--publish", action="store_true", help="Publish directly to Redpanda/Kafka topics")
    args = parser.parse_args()

    simulator = PharmaSupplyChainSimulator(
        num_pharmacies=args.pharmacies,
        num_drugs=args.drugs,
        sim_days=args.days,
        time_dilation=args.dilation
    )

    if args.publish:
        from streaming.producer import StreamProducer
        producer = StreamProducer()
        simulator.run_simulation(publish_callback=producer.publish_batch)
        producer.close()
    else:
        simulator.run_simulation()

