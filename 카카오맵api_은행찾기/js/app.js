(() => {
  "use strict";

  const GANGNAM_STATION = { lat: 37.49818, lng: 127.027386 };
  const ORIGIN = { name: "멀티캠퍼스 역삼", lat: 37.5012743, lng: 127.039585 };
  const MAX_SEARCH_PAGES = 3;

  const state = {
    map: null,
    places: null,
    infoWindow: null,
    markers: [],
    routePolyline: null,
    originMarker: null,
    activePlaceKey: null,
    routeRequestId: 0,
  };

  const elements = {};

  function boot() {
    cacheElements();
    populateSelectBoxes();
    bindEvents();
    loadKakaoMapSdk();
  }

  function cacheElements() {
    elements.map = document.querySelector("#map");
    elements.form = document.querySelector("#search-form");
    elements.province = document.querySelector("#province-select");
    elements.district = document.querySelector("#district-select");
    elements.bank = document.querySelector("#bank-select");
    elements.resetButton = document.querySelector("#reset-button");
    elements.status = document.querySelector("#status-message");
    elements.resultCount = document.querySelector("#result-count");
    elements.branchList = document.querySelector("#branch-list");
    elements.routeDestination = document.querySelector("#route-destination");
    elements.routeDistance = document.querySelector("#route-distance");
  }

  function populateSelectBoxes() {
    const data = getBankData();

    appendOptions(
      elements.province,
      data.mapInfo.map((area) => ({ label: area.name, value: area.name })),
      "광역시/도를 선택하세요",
    );

    appendOptions(
      elements.bank,
      data.bankInfo.map((bank) => ({ label: bank, value: bank })),
      "은행을 선택하세요",
    );
  }

  function bindEvents() {
    elements.province.addEventListener("change", handleProvinceChange);
    elements.form.addEventListener("submit", handleSearchSubmit);
    elements.resetButton.addEventListener("click", resetSearch);
  }

  function loadKakaoMapSdk() {
    const key = getConfigValue("JAVASCRIPT_KEY");

    if (isEmptyKey(key)) {
      setStatus("js/apikey.js에 Kakao JavaScript 키를 입력하면 지도가 표시됩니다.", "warning");
      return;
    }

    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&libraries=services&autoload=false`;
    script.async = true;
    script.onload = () => {
      window.kakao.maps.load(initializeMap);
    };
    script.onerror = () => {
      setStatus("Kakao 지도 API를 불러오지 못했습니다. 키와 플랫폼 도메인을 확인하세요.", "error");
    };
    document.head.appendChild(script);
  }

  function initializeMap() {
    const kakaoMaps = window.kakao.maps;
    elements.map.textContent = "";

    const center = new kakaoMaps.LatLng(GANGNAM_STATION.lat, GANGNAM_STATION.lng);
    state.map = new kakaoMaps.Map(elements.map, {
      center,
      level: 4,
    });
    state.places = new kakaoMaps.services.Places();
    state.infoWindow = new kakaoMaps.InfoWindow({ zIndex: 3 });

    const originPosition = new kakaoMaps.LatLng(ORIGIN.lat, ORIGIN.lng);
    state.originMarker = new kakaoMaps.Marker({
      map: state.map,
      position: originPosition,
      title: ORIGIN.name,
    });

    setStatus("검색 조건을 선택한 뒤 찾기 버튼을 누르세요.", "success");
  }

  function handleProvinceChange() {
    const selectedArea = getBankData().mapInfo.find((area) => area.name === elements.province.value);
    const districts = selectedArea ? selectedArea.countries : [];

    appendOptions(
      elements.district,
      districts.map((district) => ({ label: district, value: district })),
      "시/군/구를 선택하세요",
    );
    elements.district.disabled = districts.length === 0;
  }

  async function handleSearchSubmit(event) {
    event.preventDefault();

    if (!state.map || !state.places) {
      setStatus("Kakao 지도 API가 준비된 뒤 검색할 수 있습니다.", "warning");
      return;
    }

    const province = elements.province.value;
    const district = elements.district.value;
    const bank = elements.bank.value;

    if (!province || !district || !bank) {
      setStatus("광역시/도, 시/군/구, 은행명을 모두 선택하세요.", "warning");
      return;
    }

    clearMarkers();
    clearRoute();
    resetRouteSummary();
    setStatus("은행 지점을 검색하고 있습니다.", "");

    const query = `${province} ${district} ${bank}`;
    const places = await searchPlaces(query);

    if (places.length === 0) {
      setStatus("검색 결과가 없습니다. 조건을 바꿔 다시 검색하세요.", "warning");
      updateResultCount(0);
      return;
    }

    renderPlaces(places);
    setStatus(`${query} 검색 결과입니다. 마커나 목록을 선택하면 경로를 확인할 수 있습니다.`, "success");
  }

  function searchPlaces(query) {
    const kakaoStatus = window.kakao.maps.services.Status;

    return new Promise((resolve) => {
      const collected = [];
      let loadedPages = 0;

      const callback = (results, status, pagination) => {
        if (status !== kakaoStatus.OK) {
          resolve([]);
          return;
        }

        collected.push(...results);
        loadedPages += 1;

        if (pagination.hasNextPage && loadedPages < MAX_SEARCH_PAGES) {
          pagination.nextPage();
          return;
        }

        resolve(collected);
      };

      state.places.keywordSearch(query, callback, { size: 15 });
    });
  }

  function renderPlaces(places) {
    const kakaoMaps = window.kakao.maps;
    const bounds = new kakaoMaps.LatLngBounds();
    const fragment = document.createDocumentFragment();

    places.forEach((place, index) => {
      const position = new kakaoMaps.LatLng(Number(place.y), Number(place.x));
      const marker = new kakaoMaps.Marker({
        map: state.map,
        position,
        title: place.place_name,
      });

      const placeKey = getPlaceKey(place, index);
      marker.placeKey = placeKey;
      marker.place = place;
      state.markers.push(marker);
      bounds.extend(position);

      kakaoMaps.event.addListener(marker, "click", () => {
        selectPlace(place, marker, placeKey);
      });

      fragment.appendChild(createPlaceListItem(place, marker, placeKey, index));
    });

    elements.branchList.replaceChildren(fragment);
    updateResultCount(places.length);

    if (places.length === 1) {
      state.map.setCenter(new kakaoMaps.LatLng(Number(places[0].y), Number(places[0].x)));
      state.map.setLevel(3);
      return;
    }

    state.map.setBounds(bounds);
  }

  function createPlaceListItem(place, marker, placeKey, index) {
    const item = document.createElement("li");
    item.className = "branch-item";
    item.dataset.placeKey = placeKey;

    const title = document.createElement("h3");
    title.className = "branch-title";
    title.textContent = `${index + 1}. ${place.place_name}`;

    const address = document.createElement("p");
    address.className = "branch-address";
    address.textContent = place.road_address_name || place.address_name || "주소 정보 없음";

    const phone = document.createElement("p");
    phone.className = "branch-phone";
    phone.textContent = place.phone ? `전화 ${place.phone}` : "전화 정보 없음";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "list-button";
    button.textContent = "지도에서 보기";
    button.addEventListener("click", () => {
      selectPlace(place, marker, placeKey);
    });

    item.append(title, address, phone, button);
    return item;
  }

  function selectPlace(place, marker, placeKey) {
    state.activePlaceKey = placeKey;
    highlightSelectedPlace();
    showInfoWindow(place, marker);
    state.map.panTo(marker.getPosition());
    drawRouteToPlace(place);
  }

  function highlightSelectedPlace() {
    elements.branchList.querySelectorAll(".branch-item").forEach((item) => {
      item.classList.toggle("is-active", item.dataset.placeKey === state.activePlaceKey);
    });
  }

  function showInfoWindow(place, marker) {
    const address = place.road_address_name || place.address_name || "주소 정보 없음";
    const content = `
      <div class="info-window">
        <strong>${escapeHtml(place.place_name)}</strong>
        <p>${escapeHtml(address)}</p>
      </div>
    `;

    state.infoWindow.setContent(content);
    state.infoWindow.open(state.map, marker);
  }

  async function drawRouteToPlace(place) {
    const requestId = state.routeRequestId + 1;
    state.routeRequestId = requestId;
    clearRoute(false);

    const destination = {
      name: place.place_name,
      lat: Number(place.y),
      lng: Number(place.x),
    };
    elements.routeDestination.textContent = destination.name;
    elements.routeDistance.textContent = "경로 계산 중";

    const mobilityKey = getConfigValue("MOBILITY_REST_KEY");

    if (isEmptyKey(mobilityKey)) {
      drawReferenceLine(destination);
      elements.routeDistance.textContent = "Mobility Key 필요";
      setStatus("Mobility REST Key가 없어서 목적지 확인용 참고선을 표시했습니다.", "warning");
      return;
    }

    try {
      const route = await requestMobilityRoute(destination, mobilityKey);
      if (requestId !== state.routeRequestId) {
        return;
      }
      drawMobilityRoute(route, destination);
      setStatus("Kakao Mobility API 경로를 지도에 표시했습니다.", "success");
    } catch (error) {
      if (requestId !== state.routeRequestId) {
        return;
      }
      console.error(error);
      drawReferenceLine(destination);
      elements.routeDistance.textContent = "경로 API 호출 실패";
      setStatus("Mobility API 호출에 실패해 목적지 확인용 참고선을 표시했습니다.", "warning");
    }
  }

  async function requestMobilityRoute(destination, mobilityKey) {
    const url = new URL("https://apis-navi.kakaomobility.com/v1/directions");
    url.searchParams.set("origin", `${ORIGIN.lng},${ORIGIN.lat}`);
    url.searchParams.set("destination", `${destination.lng},${destination.lat}`);
    url.searchParams.set("priority", "RECOMMEND");

    const response = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `KakaoAK ${mobilityKey}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Mobility API error: ${response.status}`);
    }

    return response.json();
  }

  function drawMobilityRoute(routeResponse, destination) {
    const kakaoMaps = window.kakao.maps;
    const route = routeResponse.routes && routeResponse.routes[0];

    if (!route || !Array.isArray(route.sections)) {
      throw new Error("Mobility API 응답에 경로 데이터가 없습니다.");
    }

    const path = [];

    route.sections.forEach((section) => {
      section.roads.forEach((road) => {
        for (let index = 0; index < road.vertexes.length; index += 2) {
          const lng = road.vertexes[index];
          const lat = road.vertexes[index + 1];
          path.push(new kakaoMaps.LatLng(lat, lng));
        }
      });
    });

    if (path.length === 0) {
      throw new Error("Polyline으로 표시할 좌표가 없습니다.");
    }

    state.routePolyline = new kakaoMaps.Polyline({
      map: state.map,
      path,
      strokeWeight: 6,
      strokeColor: "#2563eb",
      strokeOpacity: 0.9,
      strokeStyle: "solid",
    });

    fitRouteBounds(path);

    const summary = route.summary || {};
    elements.routeDistance.textContent = `${formatDistance(summary.distance)} / ${formatDuration(summary.duration)}`;
    elements.routeDestination.textContent = destination.name;
  }

  function drawReferenceLine(destination) {
    const kakaoMaps = window.kakao.maps;
    const path = [
      new kakaoMaps.LatLng(ORIGIN.lat, ORIGIN.lng),
      new kakaoMaps.LatLng(destination.lat, destination.lng),
    ];

    state.routePolyline = new kakaoMaps.Polyline({
      map: state.map,
      path,
      strokeWeight: 5,
      strokeColor: "#f97316",
      strokeOpacity: 0.85,
      strokeStyle: "shortdash",
    });

    fitRouteBounds(path);
  }

  function fitRouteBounds(path) {
    const kakaoMaps = window.kakao.maps;
    const bounds = new kakaoMaps.LatLngBounds();
    bounds.extend(new kakaoMaps.LatLng(ORIGIN.lat, ORIGIN.lng));
    path.forEach((point) => bounds.extend(point));
    state.map.setBounds(bounds);
  }

  function clearMarkers() {
    state.markers.forEach((marker) => marker.setMap(null));
    state.markers = [];
    state.activePlaceKey = null;
    elements.branchList.replaceChildren();
    updateResultCount(0);

    if (state.infoWindow) {
      state.infoWindow.close();
    }
  }

  function clearRoute(invalidate = true) {
    if (invalidate) {
      state.routeRequestId += 1;
    }

    if (state.routePolyline) {
      state.routePolyline.setMap(null);
      state.routePolyline = null;
    }
  }

  function resetSearch() {
    elements.form.reset();
    appendOptions(elements.district, [], "시/군/구를 선택하세요");
    elements.district.disabled = true;
    clearMarkers();
    clearRoute();
    resetRouteSummary();

    if (state.map) {
      const center = new window.kakao.maps.LatLng(GANGNAM_STATION.lat, GANGNAM_STATION.lng);
      state.map.setCenter(center);
      state.map.setLevel(4);
      setStatus("검색 조건을 선택한 뒤 찾기 버튼을 누르세요.", "success");
    } else {
      setStatus("js/apikey.js에 Kakao JavaScript 키를 입력하면 지도가 표시됩니다.", "warning");
    }
  }

  function resetRouteSummary() {
    elements.routeDestination.textContent = "은행을 선택하세요";
    elements.routeDistance.textContent = "-";
  }

  function appendOptions(select, options, placeholder) {
    const fragment = document.createDocumentFragment();
    const placeholderOption = document.createElement("option");
    placeholderOption.value = "";
    placeholderOption.textContent = placeholder;
    fragment.appendChild(placeholderOption);

    options.forEach(({ label, value }) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      fragment.appendChild(option);
    });

    select.replaceChildren(fragment);
  }

  function updateResultCount(count) {
    elements.resultCount.textContent = `${count}개`;
  }

  function setStatus(message, type) {
    elements.status.textContent = message;
    elements.status.className = "status-message";

    if (type) {
      elements.status.classList.add(`is-${type}`);
    }
  }

  function getBankData() {
    return window.BANK_DATA || { mapInfo: [], bankInfo: [] };
  }

  function getConfigValue(name) {
    const config = window.KAKAO_CONFIG || {};
    return String(config[name] || "").trim();
  }

  function isEmptyKey(value) {
    return !value || value.includes("발급받은") || value.includes("YOUR_") || value.includes("선택_사항");
  }

  function getPlaceKey(place, index) {
    return place.id || `${place.x}-${place.y}-${index}`;
  }

  function escapeHtml(value) {
    const htmlEntities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };

    return String(value).replace(/[&<>"']/g, (char) => htmlEntities[char]);
  }

  function formatDistance(distance) {
    if (typeof distance !== "number") {
      return "거리 정보 없음";
    }

    if (distance < 1000) {
      return `${Math.round(distance)}m`;
    }

    return `${(distance / 1000).toFixed(1)}km`;
  }

  function formatDuration(duration) {
    if (typeof duration !== "number") {
      return "시간 정보 없음";
    }

    const minutes = Math.max(1, Math.round(duration / 60));
    const hours = Math.floor(minutes / 60);
    const remainMinutes = minutes % 60;

    if (hours === 0) {
      return `${minutes}분`;
    }

    if (remainMinutes === 0) {
      return `${hours}시간`;
    }

    return `${hours}시간 ${remainMinutes}분`;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
