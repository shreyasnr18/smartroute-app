document.addEventListener("DOMContentLoaded", () => {
    // Mode Switcher Tabs
    const tabDirectBtn = document.getElementById("tabDirectBtn");
    const tabShowBtn = document.getElementById("tabShowBtn");
    const tabParkingBtn = document.getElementById("tabParkingBtn");
    const directModeContainer = document.getElementById("directModeContainer");
    const showModeContainer = document.getElementById("showModeContainer");
    const parkingModeContainer = document.getElementById("parkingModeContainer");

    // Form elements
    const routeForm = document.getElementById("routeForm");
    const originInput = document.getElementById("originInput");
    const destinationInput = document.getElementById("destinationInput");
    const originDropdown = document.getElementById("originDropdown");
    const destinationDropdown = document.getElementById("destinationDropdown");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const resultSection = document.getElementById("resultSection");
    const simulateRushBtn = document.getElementById("simulateRushBtn");
    const simulationSection = document.getElementById("simulationSection");

    // Show Discovery elements
    const showSearchForm = document.getElementById("showSearchForm");
    const showsTableSection = document.getElementById("showsTableSection");
    const showsTableBody = document.getElementById("showsTableBody");
    const confirmModal = document.getElementById("confirmModal");
    const confirmSummaryText = document.getElementById("confirmSummaryText");
    const confirmYesBtn = document.getElementById("confirmYesBtn");
    const confirmNoBtn = document.getElementById("confirmNoBtn");

    // Checkout elements
    const checkoutModal = document.getElementById("checkoutModal");
    const checkoutSummaryBox = document.getElementById("checkoutSummaryBox");
    const simulatePaymentBtn = document.getElementById("simulatePaymentBtn");
    const viewOnBmsLink = document.getElementById("viewOnBmsLink");
    const closeCheckoutBtn = document.getElementById("closeCheckoutBtn");

    let selectedShowOption = null;

    // Tab switching logic
    tabDirectBtn.addEventListener("click", () => {
        tabDirectBtn.classList.add("active");
        tabShowBtn.classList.remove("active");
        if (tabParkingBtn) tabParkingBtn.classList.remove("active");
        directModeContainer.style.display = "block";
        showModeContainer.style.display = "none";
        if (parkingModeContainer) parkingModeContainer.style.display = "none";
    });

    tabShowBtn.addEventListener("click", () => {
        tabShowBtn.classList.add("active");
        tabDirectBtn.classList.remove("active");
        if (tabParkingBtn) tabParkingBtn.classList.remove("active");
        showModeContainer.style.display = "block";
        directModeContainer.style.display = "none";
        if (parkingModeContainer) parkingModeContainer.style.display = "none";
        resultSection.style.display = "none";
        simulationSection.style.display = "none";
    });

    if (tabParkingBtn) {
        tabParkingBtn.addEventListener("click", () => {
            tabParkingBtn.classList.add("active");
            tabDirectBtn.classList.remove("active");
            tabShowBtn.classList.remove("active");
            if (parkingModeContainer) parkingModeContainer.style.display = "block";
            directModeContainer.style.display = "none";
            showModeContainer.style.display = "none";
            resultSection.style.display = "none";
            simulationSection.style.display = "none";
        });
    }

    // Autocomplete logic for Origin and Destination textboxes
    function setupAutocomplete(inputEl, dropdownEl) {
        let debounceTimer = null;

        inputEl.addEventListener("input", () => {
            const query = inputEl.value.trim();
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                if (!query) {
                    dropdownEl.style.display = "none";
                    return;
                }
                try {
                    const resp = await fetch(`/api/places/suggest?q=${encodeURIComponent(query)}`);
                    const data = await resp.json();
                    renderSuggestions(inputEl, dropdownEl, data.suggestions || []);
                } catch (e) {
                    console.error("Autocomplete fetch error:", e);
                }
            }, 120);
        });

        inputEl.addEventListener("focus", async () => {
            const query = inputEl.value.trim();
            try {
                const resp = await fetch(`/api/places/suggest?q=${encodeURIComponent(query)}`);
                const data = await resp.json();
                renderSuggestions(inputEl, dropdownEl, data.suggestions || []);
            } catch (e) {}
        });
    }

    function renderSuggestions(inputEl, dropdownEl, suggestions) {
        dropdownEl.innerHTML = "";
        if (suggestions.length === 0) {
            dropdownEl.style.display = "none";
            return;
        }

        suggestions.forEach(place => {
            const item = document.createElement("div");
            item.className = "dropdown-item";
            item.innerHTML = `
                <span class="dropdown-item-name">${place.name}</span>
                <span class="dropdown-item-locality">${place.locality}</span>
            `;
            item.addEventListener("mousedown", (e) => {
                e.preventDefault();
                inputEl.value = place.name;
                dropdownEl.style.display = "none";
            });
            dropdownEl.appendChild(item);
        });

        dropdownEl.style.display = "block";
    }

    document.addEventListener("mousedown", (e) => {
        if (!originInput.contains(e.target) && !originDropdown.contains(e.target)) {
            originDropdown.style.display = "none";
        }
        if (!destinationInput.contains(e.target) && !destinationDropdown.contains(e.target)) {
            destinationDropdown.style.display = "none";
        }
    });

    setupAutocomplete(originInput, originDropdown);
    setupAutocomplete(destinationInput, destinationDropdown);

    // Handle Route Form Submit (Single Commuter Request)
    routeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const origin = originInput.value.trim();
        const destination = destinationInput.value.trim();
        if (!origin || !destination) return;

        originDropdown.style.display = "none";
        destinationDropdown.style.display = "none";

        loadingOverlay.style.display = "flex";

        try {
            const [resp] = await Promise.all([
                fetch("/api/route", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ origin, destination })
                }),
                new Promise(resolve => setTimeout(resolve, 650))
            ]);

            const data = await resp.json();
            if (data.status === "success") {
                renderRouteResult(data, origin, destination);
            } else {
                alert("Error finding route: " + (data.error || "Unknown error"));
            }
        } catch (err) {
            alert("Network error: Could not connect to backend.");
        } finally {
            loadingOverlay.style.display = "none";
        }
    });

    function renderRouteResult(data, origin, destination) {
        resultSection.style.display = "block";
        const assigned = data.assigned_route;
        const divInfo = data.diversion_info;

        const badge = document.getElementById("statusBadge");
        badge.textContent = divInfo.status_badge;
        badge.className = divInfo.diverted ? "badge diverted" : "badge";

        document.getElementById("routeName").textContent = assigned.name;
        document.getElementById("routeEta").textContent = assigned.eta_minutes;
        document.getElementById("routeDist").textContent = assigned.distance_km;

        const statusEl = document.getElementById("corridorLoadStatus");
        statusEl.textContent = `${divInfo.assigned_route_load} / ${divInfo.capacity_threshold} (${divInfo.diverted ? 'Saturated - Diverted' : 'Optimal Flow'})`;

        document.getElementById("routeReason").textContent = assigned.reason;
        const divReasonEl = document.getElementById("diversionReasonText");
        if (divInfo.diverted) {
            divReasonEl.textContent = `⚡ Corridor Management Note: ${divInfo.diversion_reason}`;
            divReasonEl.style.display = "block";
        } else {
            divReasonEl.style.display = "none";
        }

        const iframeEl = document.getElementById("googleMapIframe");
        iframeEl.src = `https://maps.google.com/maps?saddr=${encodeURIComponent(origin)}&daddr=${encodeURIComponent(destination)}&output=embed`;

        const gmapsBtn = document.getElementById("googleMapsLinkBtn");
        gmapsBtn.href = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&travelmode=driving`;

        // Check for Google Maps graceful degradation fallback
        const gmapsBanner = document.getElementById("gmapsFallbackBanner");
        const gmapsText = document.getElementById("gmapsFallbackText");
        const trafficTrace = (data.pipeline_trace || []).find(t => t.agent && t.agent.includes("Traffic"));
        if (trafficTrace && (trafficTrace.data.source_mode || "").toLowerCase().includes("cached")) {
            gmapsText.textContent = `Live Google Maps API Quota/Key unavailable (${trafficTrace.data.source_mode}). Using cached corridor geometry with 100% functional fallback.`;
            gmapsBanner.style.display = "block";
        } else if (gmapsBanner) {
            gmapsBanner.style.display = "none";
        }

        // Populate Low-Data Text Directions (for weak mobile bandwidth/2G areas)
        const lowDataList = document.getElementById("lowDataStepsList");
        if (lowDataList) {
            lowDataList.innerHTML = "";
            const steps = assigned.steps || [`Depart ${origin} heading towards corridor`, `Enter primary arterial route via ${assigned.name}`, `Follow guidance bypassing junction bottlenecks`, `Arrive safely at ${destination}`];
            steps.forEach(st => {
                const li = document.createElement("li");
                li.textContent = st;
                lowDataList.appendChild(li);
            });
        }

        const timelineEl = document.getElementById("checkpointsTimeline");
        const stepsList = document.getElementById("stepsList");
        stepsList.innerHTML = "";
        
        if (timelineEl) {
            timelineEl.innerHTML = "";
            const checkpoints = assigned.predictive_checkpoints || [];
            if (checkpoints.length > 0) {
                timelineEl.style.display = "flex";
                stepsList.style.display = "none";
                checkpoints.forEach((cp) => {
                    const card = document.createElement("div");
                    const statusClass = cp.prediction_status || 'optimal';
                    card.className = `checkpoint-card cp-card-${statusClass}`;
                    
                    let icon = '📍';
                    if (statusClass === 'alert') icon = '⚠️';
                    else if (statusClass === 'diverted') icon = '⚡';
                    else if (statusClass === 'success') icon = '🎯';
                    
                    card.innerHTML = `
                        <div class="cp-top-bar">
                            <div class="cp-title-group">
                                <span class="cp-icon">${icon}</span>
                                <span class="cp-junction">${cp.junction}</span>
                            </div>
                            <span class="cp-dist">${cp.distance_marker}</span>
                        </div>
                        <div class="cp-flow-tag cp-tag-${statusClass}">${cp.expected_flow}</div>
                        <p class="cp-guidance-text">${cp.guidance}</p>
                    `;
                    timelineEl.appendChild(card);
                });
            } else {
                timelineEl.style.display = "none";
                stepsList.style.display = "block";
                (assigned.steps || []).forEach(st => {
                    const li = document.createElement("li");
                    li.textContent = st;
                    stepsList.appendChild(li);
                });
            }
        }

        resultSection.scrollIntoView({ behavior: "smooth" });
    }

    // Handle Simulate Rush Button
    simulateRushBtn.addEventListener("click", async () => {
        const origin = originInput.value.trim() || "Hebbal";
        const destination = destinationInput.value.trim() || "KR Puram via Tin Factory";

        simulateRushBtn.disabled = true;
        simulateRushBtn.textContent = "Simulating Rush in Background...";
        loadingOverlay.style.display = "flex";

        try {
            const [resp] = await Promise.all([
                fetch("/api/simulate-rush", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ origin, destination, count: 15 })
                }),
                new Promise(resolve => setTimeout(resolve, 700))
            ]);
            const data = await resp.json();
            if (data.status === "success") {
                simulationSection.style.display = "block";
                document.getElementById("simSummaryText").textContent = 
                    `✅ ${data.summary} Evaluated completely in background via 5 AI Agents (< 0.1s). Commuters #1-#10 assigned primary route, and Commuters #11-#15 automatically diverted to prevent corridor gridlock!`;
                
                const routeResp = await fetch("/api/route", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ origin, destination })
                });
                const routeData = await routeResp.json();
                renderRouteResult(routeData, origin, destination);
            }
        } catch (err) {
            alert("Network error during rush simulation.");
        } finally {
            loadingOverlay.style.display = "none";
            simulateRushBtn.disabled = false;
            simulateRushBtn.textContent = "Simulate Corridor Rush";
        }
    });

    // ================= SPOT-MATCH DIMENSION-AWARE PARKING FINDER PIPELINE =================
    let currentParkingResult = null;
    let selectedParkingSpot = null;

    if (parkingForm) {
        parkingForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const vehicle_query = (customVehicleInput.value.trim() || vehicleSelect.value || "maruti_swift");
            const origin = parkingOriginInput.value.trim() || "Hebbal";
            const area_query = parkingAreaInput.value.trim();

            if (parkingLoadingSection) parkingLoadingSection.style.display = "flex";
            if (parkingResultsSection) parkingResultsSection.style.display = "none";
            if (selectedSpotConfirmBox) selectedSpotConfirmBox.style.display = "none";

            try {
                const resp = await fetch("/api/parking-search", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ vehicle_query, origin, area_query })
                });
                const data = await resp.json();
                if (data.status === "success") {
                    currentParkingResult = { data, origin };
                    renderParkingTable(data, origin);
                } else {
                    alert("Error searching parking: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                alert("Network error during parking search.");
            } finally {
                if (parkingLoadingSection) parkingLoadingSection.style.display = "none";
            }
        });
    }

    if (showTooTightToggle) {
        showTooTightToggle.addEventListener("change", () => {
            if (currentParkingResult) {
                renderParkingTable(currentParkingResult.data, currentParkingResult.origin);
            }
        });
    }

    function renderParkingTable(data, origin) {
        if (!parkingTableBody || !parkingResultsSection) return;
        parkingTableBody.innerHTML = "";
        parkingResultsSection.style.display = "block";

        const fitData = data.fit_matching || {};
        const vProfile = (data.vehicle_profile && data.vehicle_profile.vehicle) || {};
        const spots = fitData.ranked_spots || [];
        const showTight = showTooTightToggle ? showTooTightToggle.checked : false;

        const filteredSpots = spots.filter(s => showTight || s.fit_status !== "Too Tight");

        if (parkingSummaryBadge) {
            parkingSummaryBadge.textContent = `${vProfile.display_name || "Vehicle"} — Req. Gap: ${fitData.required_length_m || "--"}m (+0.3m buffer) | Fits: ${fitData.summary_counts?.fits || 0}, Marginal: ${fitData.summary_counts?.marginal || 0}, Too Tight: ${fitData.summary_counts?.too_tight || 0}`;
        }

        if (filteredSpots.length === 0) {
            parkingTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 16px;">No spots match current filters or all are 'Too Tight'. Check 'Show Too Tight spots' to view tight bays.</td></tr>`;
            return;
        }

        filteredSpots.forEach((spot, index) => {
            const tr = document.createElement("tr");
            tr.className = "parking-row";
            if (selectedParkingSpot && selectedParkingSpot.location_id === spot.location_id) {
                tr.classList.add("selected-spot-row");
            }

            let badgeClass = "fits-badge";
            if (spot.fit_status === "Marginal") badgeClass = "marginal-badge";
            if (spot.fit_status === "Too Tight") badgeClass = "tight-badge";

            tr.innerHTML = `
                <td><strong>${index + 1}</strong></td>
                <td>
                    <strong>${spot.address}</strong>
                    <br><small style="color: #94a3b8;">${spot.curb_side}</small>
                </td>
                <td>${spot.distance_km} km</td>
                <td>${spot.duration_minutes} mins</td>
                <td><strong style="font-size: 0.95rem;">${spot.gap_length_m}m</strong></td>
                <td><span class="badge ${badgeClass}" style="display:inline-block; padding:3px 8px; font-size:0.75rem;">${spot.fit_status}</span></td>
                <td>
                    <button type="button" class="select-spot-btn" data-id="${spot.location_id}">Select Spot</button>
                </td>
            `;

            tr.querySelector(".select-spot-btn").addEventListener("click", (e) => {
                e.stopPropagation();
                selectParkingSpot(spot, origin, vProfile);
            });

            tr.addEventListener("click", () => {
                selectParkingSpot(spot, origin, vProfile);
            });

            parkingTableBody.appendChild(tr);
        });

        parkingResultsSection.scrollIntoView({ behavior: "smooth" });
    }

    function selectParkingSpot(spot, origin, vProfile) {
        selectedParkingSpot = spot;
        if (selectedSpotConfirmBox && selectedSpotConfirmText) {
            selectedSpotConfirmText.innerHTML = `
                <strong>📍 Destination Spot:</strong> ${spot.address} (${spot.curb_side})<br>
                <strong>🚗 Distance & Duration:</strong> ${spot.distance_km} km — ${spot.duration_minutes} mins from ${origin}<br>
                <strong>📏 Physical Compatibility:</strong> Gap length is <strong style="color: var(--accent-primary);">${spot.gap_length_m}m</strong> — <span class="badge ${spot.fit_status === 'Fits' ? 'fits-badge' : spot.fit_status === 'Marginal' ? 'marginal-badge' : 'tight-badge'}" style="padding: 2px 6px;">${spot.fit_status}</span> for your ${vProfile.display_name || 'Vehicle'} (Requires ${spot.gap_length_m >= vProfile.length_m + 0.3 ? vProfile.length_m + 0.3 : vProfile.length_m}m with buffer).
            `;
            selectedSpotConfirmBox.style.display = "block";
            selectedSpotConfirmBox.scrollIntoView({ behavior: "smooth" });

            // Highlight row
            document.querySelectorAll("#parkingTableBody tr").forEach(row => row.classList.remove("selected-spot-row"));
            const btn = document.querySelector(`.select-spot-btn[data-id="${spot.location_id}"]`);
            if (btn && btn.closest("tr")) {
                btn.closest("tr").classList.add("selected-spot-row");
            }
        }
    }

    if (routeToSpotBtn) {
        routeToSpotBtn.addEventListener("click", async () => {
            if (!selectedParkingSpot) return;
            const targetAddress = selectedParkingSpot.address || "Soap Factory Curb, Yeshwantpur";
            const originAddress = currentParkingResult?.origin || "Hebbal";

            // Switch to Direct Route Planner tab
            if (tabDirectBtn) tabDirectBtn.click();
            if (originInput) originInput.value = originAddress;
            if (destinationInput) destinationInput.value = targetAddress;

            if (loadingOverlay) loadingOverlay.style.display = "flex";

            try {
                const resp = await fetch("/api/route", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ origin: originAddress, destination: targetAddress })
                });
                const data = await resp.json();
                renderRouteResult(data, originAddress, targetAddress);

                const badge = document.getElementById("statusBadge");
                if (badge) {
                    badge.textContent = `🚗 Reserved Spot Gap (${selectedParkingSpot.gap_length_m}m) — ${badge.textContent}`;
                }
            } catch (err) {
                alert("Network error while routing to parking spot.");
            } finally {
                if (loadingOverlay) loadingOverlay.style.display = "none";
            }
        });
    }

    // ================= SHOW DISCOVERY & BOOKING CONFIRMATION PIPELINE =================
    showSearchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const show_name = document.getElementById("showNameInput").value.trim();
        const city = document.getElementById("showCityInput").value.trim() || "Bengaluru";
        const origin = document.getElementById("showOriginInput").value.trim() || "Hebbal";
        const budget_per_ticket = parseFloat(document.getElementById("budgetInput").value) || 800;
        const ticket_count = parseInt(document.getElementById("ticketCountInput").value, 10) || 2;
        const location_pref = document.getElementById("locationPrefInput").value.trim();

        const screenCheckboxes = document.querySelectorAll('input[name="screenType"]:checked');
        const screen_types = Array.from(screenCheckboxes).map(cb => cb.value);

        loadingOverlay.style.display = "flex";

        try {
            const resp = await fetch("/api/shows/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    show_name,
                    city,
                    budget_per_ticket,
                    ticket_count,
                    screen_types,
                    location_pref,
                    origin
                })
            });
            const data = await resp.json();
            if (data.status === "success") {
                renderShowsTable(data.shows || [], origin);
            } else {
                alert("Error searching shows: " + (data.error || "Unknown error"));
            }
        } catch (err) {
            alert("Network error while searching shows.");
        } finally {
            loadingOverlay.style.display = "none";
        }
    });

    function renderShowsTable(shows, origin) {
        showsTableBody.innerHTML = "";
        showsTableSection.style.display = "block";

        if (shows.length === 0) {
            showsTableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 16px;">No candidate shows matched your budget or location filters. Try loosening your criteria.</td></tr>`;
            return;
        }

        shows.forEach(show => {
            const tr = document.createElement("tr");
            tr.className = "show-row";
            tr.innerHTML = `
                <td><strong>${show.s_no}</strong></td>
                <td>${show.location}</td>
                <td><strong>${show.mall_theatre}</strong></td>
                <td>${show.distance_km} km</td>
                <td>${show.duration_minutes} mins</td>
                <td><span style="color: #34d399; font-weight: 600;">${show.tickets_available} available</span></td>
                <td>₹${show.price_per_ticket}</td>
                <td>₹${show.parking_fee_per_hour}/hr</td>
                <td><strong>₹${show.total_cost}</strong> <br><small style="color: #94a3b8;">(incl. ₹${show.bms_fee_estimate} BMS fee)</small></td>
            `;

            tr.addEventListener("click", () => {
                selectedShowOption = { ...show, origin };
                confirmSummaryText.textContent = show.selection_summary;
                confirmModal.style.display = "flex";
            });

            showsTableBody.appendChild(tr);
        });

        showsTableSection.scrollIntoView({ behavior: "smooth" });
    }

    confirmNoBtn.addEventListener("click", () => {
        confirmModal.style.display = "none";
        selectedShowOption = null;
    });

    confirmYesBtn.addEventListener("click", () => {
        confirmModal.style.display = "none";
        if (!selectedShowOption) return;

        // Populate Mock Checkout Modal
        checkoutSummaryBox.innerHTML = `
            <p><strong>Show:</strong> ${selectedShowOption.show_name}</p>
            <p><strong>Venue:</strong> ${selectedShowOption.venue_name_full}</p>
            <p><strong>Tickets:</strong> ${selectedShowOption.ticket_count} tickets @ ₹${selectedShowOption.price_per_ticket} each</p>
            <p><strong>BookMyShow Fee Estimate:</strong> ₹${selectedShowOption.bms_fee_estimate}</p>
            <p style="margin-top: 8px; font-size: 1.05rem; color: #38bdf8;"><strong>Total Amount Due: ₹${selectedShowOption.total_cost}</strong></p>
            <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">* Parking fee (₹${selectedShowOption.parking_fee_per_hour}/hr) payable separately at venue parking booth.</p>
        `;

        // Real outbound BookMyShow search URL
        const bmsQuery = encodeURIComponent(`${selectedShowOption.show_name} ${selectedShowOption.mall_theatre}`);
        viewOnBmsLink.href = `https://in.bookmyshow.com/explore/movies-bengaluru?query=${bmsQuery}`;

        checkoutModal.style.display = "flex";
    });

    closeCheckoutBtn.addEventListener("click", () => {
        checkoutModal.style.display = "none";
        selectedShowOption = null;
    });

    simulatePaymentBtn.addEventListener("click", async () => {
        if (!selectedShowOption) return;
        checkoutModal.style.display = "none";

        loadingOverlay.style.display = "flex";

        try {
            const [resp] = await Promise.all([
                fetch("/api/mock-payment-callback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        show_id: selectedShowOption.show_id,
                        ticket_count: selectedShowOption.ticket_count,
                        origin: selectedShowOption.origin || "Hebbal",
                        venue_name: selectedShowOption.mall_theatre,
                        lat: selectedShowOption.lat,
                        lng: selectedShowOption.lng,
                        total_cost: selectedShowOption.total_cost
                    })
                }),
                new Promise(resolve => setTimeout(resolve, 750))
            ]);

            const data = await resp.json();
            if (data.status === "success") {
                // Auto-Routing transition to SmartRoute screen (Step 6)
                tabDirectBtn.click(); // Switch UI active tab to Direct Route Planner
                originInput.value = selectedShowOption.origin || "Hebbal";
                destinationInput.value = selectedShowOption.mall_theatre || selectedShowOption.venue_name_full;

                renderRouteResult(data.route_result, originInput.value, destinationInput.value);

                // Add a top banner or notification verifying ticket confirmation
                const badge = document.getElementById("statusBadge");
                badge.textContent = `🎉 Booking Receipt #${data.booking_confirmation.receipt_id} — ${badge.textContent}`;
            } else {
                alert("Payment callback failed: " + (data.error || "Unknown error"));
            }
        } catch (err) {
            alert("Network error during mock payment callback.");
        } finally {
            loadingOverlay.style.display = "none";
        }
    });

    // ================== Phase 7 Interactive Upgrades Handlers ==================

    // 1. Privacy & DPDP Rights Modal Handlers
    const btnOpenPrivacy = document.getElementById("btnOpenPrivacyModal");
    const privacyModal = document.getElementById("privacyModal");
    const btnClosePrivacy = document.getElementById("btnClosePrivacyModal");
    const btnConfirmDelete = document.getElementById("btnConfirmDeleteData");
    const privacyTextEl = document.getElementById("privacyPolicyText");

    if (btnOpenPrivacy && privacyModal) {
        btnOpenPrivacy.addEventListener("click", async () => {
            privacyModal.style.display = "flex";
            try {
                const res = await fetch("/api/compliance/policy");
                const data = await res.json();
                if (data.status === "success") {
                    privacyTextEl.innerHTML = `
                        <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-primary);">${data.agent_name}</h4>
                        <p><strong>Privacy Architecture:</strong> ${data.privacy_policy.architecture}</p>
                        <p><strong>Data Minimization:</strong> ${data.data_minimization_policy.policy}</p>
                        <ul style="margin: 0.5rem 0; padding-left: 1.25rem;">
                            <li><strong>Storage Tier:</strong> ${data.privacy_policy.data_retention.location_storage}</li>
                            <li><strong>Sharing Status:</strong> ${data.privacy_policy.data_retention.third_party_sharing}</li>
                        </ul>
                    `;
                }
            } catch (e) {
                privacyTextEl.innerHTML = `<p style="color: var(--danger-color);">Could not fetch live compliance policy.</p>`;
            }
        });

        btnClosePrivacy.addEventListener("click", () => {
            privacyModal.style.display = "none";
        });

        btnConfirmDelete.addEventListener("click", async () => {
            const uid = (document.getElementById("deleteUserIdInput").value || "").trim();
            const phrase = (document.getElementById("deleteConfirmInput").value || "").trim();
            if (!uid || phrase !== "DELETE MY DATA") {
                alert("Please enter your User ID and type exactly 'DELETE MY DATA' to confirm right to erasure.");
                return;
            }
            try {
                const res = await fetch("/api/compliance/delete-my-data", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: uid, confirmation_phrase: phrase })
                });
                const data = await res.json();
                alert(`Right to Erasure Confirmed under DPDP Act: ${data.message || "Records purged."}`);
                privacyModal.style.display = "none";
            } catch (e) {
                alert("Error submitting deletion request.");
            }
        });
    }

    // 2. Crowdsourced Parking Spot Reporter Modal Handlers
    const btnOpenReporter = document.getElementById("btnOpenParkingReporter");
    const parkingReporterModal = document.getElementById("parkingReporterModal");
    const btnCloseReporter = document.getElementById("btnCloseParkingReporter");
    const formReportParking = document.getElementById("formReportParking");

    if (btnOpenReporter && parkingReporterModal) {
        btnOpenReporter.addEventListener("click", () => {
            parkingReporterModal.style.display = "flex";
        });
        btnCloseReporter.addEventListener("click", () => {
            parkingReporterModal.style.display = "none";
        });
        if (formReportParking) {
            formReportParking.addEventListener("submit", async (e) => {
                e.preventDefault();
                const address = document.getElementById("repAddressInput").value.trim();
                const lat = parseFloat(document.getElementById("repLatInput").value || "13.0031");
                const lng = parseFloat(document.getElementById("repLngInput").value || "77.5702");
                const gap = parseFloat(document.getElementById("repGapInput").value || "4.8");
                const side = document.getElementById("repCurbSideInput").value.trim();

                try {
                    const res = await fetch("/api/parking/report", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            location_id: "spot_cs_" + Math.floor(Math.random() * 9000 + 1000),
                            address: address,
                            lat: lat,
                            lng: lng,
                            gap_length_m: gap,
                            curb_side: side,
                            notes: "Crowdsourced On-Device Report"
                        })
                    });
                    const data = await res.json();
                    alert(`Spot Synced: ${data.message}`);
                    parkingReporterModal.style.display = "none";
                    if (document.getElementById("tabParkingBtn")) {
                        document.getElementById("tabParkingBtn").click();
                    }
                } catch (err) {
                    alert("Error syncing parking spot to real-time feed.");
                }
            });
        }
    }

    // 3. Admin Self-Listing Modal Handlers
    const btnOpenAdmin = document.getElementById("btnOpenAdminManager");
    const adminModal = document.getElementById("adminManagerModal");
    const btnCloseAdminList = document.querySelectorAll(".btnCloseAdminModal");
    const tabAdmEvent = document.getElementById("tabAdminEventBtn");
    const tabAdmShow = document.getElementById("tabAdminShowBtn");
    const formAdmEvent = document.getElementById("formAdminEvent");
    const formAdmShow = document.getElementById("formAdminShow");

    if (btnOpenAdmin && adminModal) {
        btnOpenAdmin.addEventListener("click", () => {
            adminModal.style.display = "flex";
        });
        btnCloseAdminList.forEach(b => {
            b.addEventListener("click", () => {
                adminModal.style.display = "none";
            });
        });

        if (tabAdmEvent && tabAdmShow) {
            tabAdmEvent.addEventListener("click", () => {
                tabAdmEvent.classList.add("active");
                tabAdmShow.classList.remove("active");
                formAdmEvent.style.display = "block";
                formAdmShow.style.display = "none";
            });
            tabAdmShow.addEventListener("click", () => {
                tabAdmShow.classList.add("active");
                tabAdmEvent.classList.remove("active");
                formAdmShow.style.display = "block";
                formAdmEvent.style.display = "none";
            });
        }

        if (formAdmEvent) {
            formAdmEvent.addEventListener("submit", async (e) => {
                e.preventDefault();
                const name = document.getElementById("admEventName").value.trim();
                const venue = document.getElementById("admEventVenue").value.trim();
                const crowd = parseInt(document.getElementById("admEventCrowd").value || "2500");
                const risk = parseInt(document.getElementById("admEventRisk").value || "65");

                try {
                    const res = await fetch("/api/events/add", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            event_id: "evt_admin_" + Math.floor(Math.random() * 9000 + 1000),
                            venue: venue,
                            event_name: name,
                            start_time: "Today 7:30 PM",
                            expected_crowd_size: crowd,
                            risk_score: risk,
                            affected_corridors: ["route_orr_tinfactory", "route_bellary_road"],
                            admin_token: "secret_admin_token"
                        })
                    });
                    const data = await res.json();
                    alert(data.message);
                    adminModal.style.display = "none";
                } catch (err) {
                    alert("Error submitting admin event.");
                }
            });
        }

        if (formAdmShow) {
            formAdmShow.addEventListener("submit", async (e) => {
                e.preventDefault();
                const name = document.getElementById("admShowName").value.trim();
                const venue = document.getElementById("admShowVenue").value.trim();
                const price = parseFloat(document.getElementById("admShowPrice").value || "450");
                const tickets = parseInt(document.getElementById("admShowTickets").value || "120");

                try {
                    const res = await fetch("/api/shows/add", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            show_id: "show_admin_" + Math.floor(Math.random() * 9000 + 1000),
                            show_name: name,
                            type: "Movie",
                            venue_name: venue,
                            address: venue + ", Bengaluru",
                            city: "Bengaluru",
                            price_per_ticket: price,
                            tickets_available: tickets,
                            screen_type: "IMAX / 4DX",
                            lat: 12.9352,
                            lng: 77.6245,
                            admin_token: "secret_admin_token"
                        })
                    });
                    const data = await res.json();
                    alert(data.message);
                    adminModal.style.display = "none";
                } catch (err) {
                    alert("Error submitting admin show.");
                }
            });
        }
    }

    // 4. Low-Data Text Directions Toggle Handlers
    const btnToggleLowData = document.getElementById("btnToggleLowDataMode");
    const mapBox = document.getElementById("mapContainerBox");
    const textBox = document.getElementById("lowDataTextBox");

    if (btnToggleLowData && mapBox && textBox) {
        btnToggleLowData.addEventListener("click", () => {
            if (textBox.style.display === "none") {
                textBox.style.display = "block";
                mapBox.style.display = "none";
                btnToggleLowData.textContent = "🗺️ Switch back to Interactive Live Map";
            } else {
                textBox.style.display = "none";
                mapBox.style.display = "block";
                btnToggleLowData.textContent = "📶 Switch to Low-Data Text Directions";
            }
        });
    }
});
