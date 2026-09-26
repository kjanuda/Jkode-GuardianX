"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import MapDetailPanel from "@/components/map/MapDetailPanel";

import type {
  GuardianMapPayload,
  GuardianMapPoint,
  MapPointType,
} from "@/types/map";


interface Props {
  data: GuardianMapPayload;
}


function MapBounds({
  points,
}: {
  points: GuardianMapPoint[];
}) {
  const map =
    useMap();

  useEffect(
    () => {
      if (
        points.length === 0
      ) {
        return;
      }

      if (
        points.length === 1
      ) {
        map.setView(
          [
            points[0].latitude,
            points[0].longitude,
          ],
          15
        );

        return;
      }

      map.fitBounds(
        points.map(
          (point) => [
            point.latitude,
            point.longitude,
          ]
        ),
        {
          padding: [
            35,
            35,
          ],
          maxZoom: 15,
        }
      );
    },
    [
      map,
      points,
    ]
  );

  return null;
}


function pointStyle(
  point: GuardianMapPoint
) {
  if (
    point.point_type ===
    "TOWER"
  ) {
    return {
      color: "#67e8f9",
      fillColor: "#22d3ee",
      fillOpacity: 0.75,
      weight: 2,
      radius: 11,
    };
  }

  if (
    point.point_type ===
    "CELL"
  ) {
    return {
      color: "#c4b5fd",
      fillColor: "#8b5cf6",
      fillOpacity: 0.7,
      weight: 2,
      radius: 8,
    };
  }

  if (
    point.active_alert
  ) {
    return {
      color: "#fca5a5",
      fillColor: "#ef4444",
      fillOpacity: 0.85,
      weight: 2,
      radius: 7,
    };
  }

  return {
    color: "#86efac",
    fillColor: "#22c55e",
    fillOpacity: 0.65,
    weight: 1.5,
    radius: 5,
  };
}


export default function NetworkMap({
  data,
}: Props) {
  const [
    visibleTypes,
    setVisibleTypes,
  ] = useState<
    Record<
      MapPointType,
      boolean
    >
  >({
    TOWER: true,
    CELL: true,
    DEVICE: true,
  });

  const [
    alertsOnly,
    setAlertsOnly,
  ] = useState(
    false
  );

  const [
    selectedPoint,
    setSelectedPoint,
  ] = useState<
    GuardianMapPoint | null
  >(
    null
  );


  const visiblePoints =
    useMemo(
      () =>
        data.points.filter(
          (point) => {
            if (
              !visibleTypes[
                point.point_type
              ]
            ) {
              return false;
            }

            if (
              alertsOnly &&
              point.point_type ===
                "DEVICE" &&
              !point.active_alert
            ) {
              return false;
            }

            return true;
          }
        ),
      [
        data.points,
        visibleTypes,
        alertsOnly,
      ]
    );


  const firstPoint =
    data.points[0];

  const initialCenter:
    [number, number] =
    firstPoint
      ? [
          firstPoint.latitude,
          firstPoint.longitude,
        ]
      : [
          0,
          0,
        ];


  function toggleType(
    type: MapPointType
  ) {
    setVisibleTypes(
      (current) => ({
        ...current,

        [type]:
          !current[
            type
          ],
      })
    );
  }


  if (
    data.points.length === 0
  ) {
    return (
      <div className="rounded-2xl border border-white/10 bg-[#070b14] p-10 text-center">
        <p className="text-sm text-white/55">
          No geolocated network points available
        </p>

        <p className="mt-2 text-xs text-white/30">
          Guardian X received no usable tower, cell or telemetry coordinates.
        </p>
      </div>
    );
  }


  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {(
          [
            "TOWER",
            "CELL",
            "DEVICE",
          ] as MapPointType[]
        ).map(
          (type) => (
            <button
              key={
                type
              }
              type="button"
              onClick={() =>
                toggleType(
                  type
                )
              }
              className={[
                "rounded-lg border px-3 py-2 text-[11px] transition",
                visibleTypes[
                  type
                ]
                  ? "border-cyan-400/20 bg-cyan-400/10 text-cyan-200"
                  : "border-white/10 bg-white/5 text-white/30",
              ].join(
                " "
              )}
            >
              {type}
            </button>
          )
        )}

        <button
          type="button"
          onClick={() =>
            setAlertsOnly(
              (current) =>
                !current
            )
          }
          className={[
            "rounded-lg border px-3 py-2 text-[11px] transition",
            alertsOnly
              ? "border-red-400/20 bg-red-400/10 text-red-200"
              : "border-white/10 bg-white/5 text-white/30",
          ].join(" ")}
        >
          Active-alert devices
        </button>

        <span className="ml-auto text-[11px] text-white/30">
          {
            visiblePoints.length
          }{" "}
          visible points
        </span>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_auto]">
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <MapContainer
            center={
              initialCenter
            }
            zoom={
              firstPoint
                ? 13
                : 2
            }
            scrollWheelZoom
            className="h-[650px] w-full bg-[#070b14]"
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapBounds
              points={
                visiblePoints
              }
            />

            {visiblePoints.map(
              (point) => {
                const style =
                  pointStyle(
                    point
                  );

                return (
                  <CircleMarker
                    key={`${point.point_type}-${point.id}`}
                    center={[
                      point.latitude,
                      point.longitude,
                    ]}
                    radius={
                      style.radius
                    }
                    pathOptions={{
                      color:
                        style.color,

                      fillColor:
                        style.fillColor,

                      fillOpacity:
                        style.fillOpacity,

                      weight:
                        style.weight,
                    }}
                    eventHandlers={{
                      click: () =>
                        setSelectedPoint(
                          point
                        ),
                    }}
                  >
                    <Popup>
                      <div className="min-w-[210px] text-sm">
                        <strong>
                          {
                            point.id
                          }
                        </strong>

                        <div className="mt-2">
                          {
                            point.point_type
                          }
                        </div>

                        <div>
                          Status:{" "}
                          {
                            point.status
                          }
                        </div>

                        <div className="mt-2 text-xs">
                          Click marker for full Guardian X context.
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              }
            )}
          </MapContainer>
        </div>

        {selectedPoint ? (
          <MapDetailPanel
            point={
              selectedPoint
            }
            data={data}
            onClose={() =>
              setSelectedPoint(
                null
              )
            }
          />
        ) : null}
      </div>

      <div className="flex flex-wrap gap-4 text-[10px] uppercase tracking-wider text-white/35">
        <span>
          ● Cyan — Tower
        </span>

        <span>
          ● Violet — Cell
        </span>

        <span>
          ● Green — Device
        </span>

        <span>
          ● Red — Active Alert
        </span>
      </div>
    </div>
  );
}
