document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const fortuneButton = document.getElementById("fortune-button");
  const fortuneResult = document.getElementById("fortune-result");
  const fuelButtons = document.getElementById("fuel-buttons");
  const fuelTrends = document.getElementById("fuel-trends");

  const fortunes = [
    {
      tone: "lucky",
      english: "Great fortune: a new opportunity will arrive before the week ends.",
      japanese: "大吉：今週末までに新しいチャンスが訪れます。",
    },
    {
      tone: "lucky",
      english: "Good fortune: your patience will be rewarded with a positive surprise.",
      japanese: "吉：あなたの忍耐は、素晴らしい驚きで報われます。",
    },
    {
      tone: "neutral",
      english: "Lucky fortune: a kind conversation will open the door to something wonderful.",
      japanese: "中吉：優しい会話が、素敵な出来事への扉を開きます。",
    },
    {
      tone: "neutral",
      english: "Fortune of focus: steady effort today will lead to a meaningful result tomorrow.",
      japanese: "小吉：今日の着実な努力は、明日の大切な結果につながります。",
    },
  ];

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities", {
        cache: "no-store",
      });
      const activities = await response.json();

      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";

        const participantsTitle = document.createElement("p");
        participantsTitle.className = "participants-title";
        participantsTitle.innerHTML = "<strong>Participants:</strong>";

        const participantsList = document.createElement("ul");
        participantsList.className = "participants-list";

        if (details.participants.length) {
          details.participants.forEach((email) => {
            const participantItem = document.createElement("li");
            participantItem.className = "participant-item";

            const participantEmail = document.createElement("span");
            participantEmail.className = "participant-email";
            participantEmail.textContent = email;

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-participant-btn";
            deleteButton.setAttribute("aria-label", `Remove ${email} from ${name}`);
            deleteButton.innerHTML = `
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">
                <path fill="currentColor" d="M9 3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1h3a1 1 0 1 1 0 2h-1v11a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V6H5a1 1 0 0 1 0-2h3V3Zm2 1v1h2V4h-2Zm-3 3v10a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V7H8Zm2 2a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1Zm4 0a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0v-5a1 1 0 0 1 1-1Z"/>
              </svg>
            `;
            deleteButton.addEventListener("click", async () => {
              await unregisterParticipant(name, email);
            });

            participantItem.appendChild(participantEmail);
            participantItem.appendChild(deleteButton);
            participantsList.appendChild(participantItem);
          });
        } else {
          const emptyItem = document.createElement("li");
          emptyItem.className = "participant-item empty";
          emptyItem.textContent = "No participants yet";
          participantsList.appendChild(emptyItem);
        }

        participantsSection.appendChild(participantsTitle);
        participantsSection.appendChild(participantsList);

        const heading = document.createElement("h4");
        heading.textContent = name;

        const description = document.createElement("p");
        description.innerHTML = `<strong>Description:</strong> ${details.description}`;

        const schedule = document.createElement("p");
        schedule.innerHTML = `<strong>Schedule:</strong> ${details.schedule}`;

        const availability = document.createElement("p");
        availability.innerHTML = `<strong>Availability:</strong> ${spotsLeft} spots left`;

        activityCard.appendChild(heading);
        activityCard.appendChild(description);
        activityCard.appendChild(schedule);
        activityCard.appendChild(availability);
        activityCard.appendChild(participantsSection);
        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function unregisterParticipant(activityName, email) {
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        await fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister participant. Please try again.", "error");
      console.error("Error unregistering participant:", error);
    }
  }

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        await fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  fortuneButton.addEventListener("click", () => {
    const fortune = fortunes[Math.floor(Math.random() * fortunes.length)];
    fortuneResult.className = `fortune-result ${fortune.tone}`;
    fortuneResult.innerHTML = `${fortune.english}<br />${fortune.japanese}`;
    fortuneResult.classList.remove("hidden");
    fortuneButton.textContent = "Reveal Another Fortune";
  });

  async function loadFuelTrends() {
    try {
      const response = await fetch("/fuel-trends", {
        cache: "no-store",
      });
      const data = await response.json();

      if (!data.months?.length || !Object.keys(data.fuelTypes || {}).length) {
        fuelTrends.innerHTML = "<p>Fuel trend data is currently unavailable.</p>";
        return;
      }

      const orderedFuelTypes = ["P98", "P95", "U91", "E10"];
      const buttons = orderedFuelTypes.filter((fuelType) => data.fuelTypes[fuelType]);

      fuelButtons.innerHTML = "";
      fuelTrends.innerHTML = "";

      buttons.forEach((fuelType) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "fuel-button";
        button.textContent = fuelType;
        button.addEventListener("click", () => {
          document.querySelectorAll(".fuel-button").forEach((btn) => btn.classList.remove("active"));
          button.classList.add("active");
          renderFuelCard(fuelType, data);
        });
        fuelButtons.appendChild(button);
      });

      const firstFuelType = buttons[0];
      if (firstFuelType) {
        const defaultButton = fuelButtons.querySelector(`.fuel-button:nth-child(1)`);
        if (defaultButton) {
          defaultButton.classList.add("active");
        }
        renderFuelCard(firstFuelType, data);
      }
    } catch (error) {
      fuelTrends.innerHTML = "<p>Failed to load fuel trends. Please try again later.</p>";
      console.error("Error fetching fuel trends:", error);
    }
  }

  function renderFuelCard(fuelType, data) {
    const details = data.fuelTypes[fuelType];
    if (!details) {
      return;
    }

    const card = document.createElement("div");
    card.className = "fuel-card";

    const title = document.createElement("h4");
    title.className = "fuel-title";
    title.textContent = `${fuelType} daily average trend`;

    const summary = document.createElement("div");
    summary.className = "fuel-summary";
    const firstPoint = details.points[0];
    const lastPoint = details.points[details.points.length - 1];
    const predictionWeek = details.trend?.next_predicted_drop_week;
    const mondayLabel = predictionWeek ? formatMondayDate(predictionWeek) : "n/a";
    summary.innerHTML = `
      <span>Range: ${firstPoint ? firstPoint.date : "n/a"} → ${lastPoint ? lastPoint.date : "n/a"}</span>
      <span>Trend: ${details.trend?.overall || "n/a"}</span>
      <span>Avg dip interval: ${details.trend?.average_weeks_between_dips ?? 0} weeks</span>
    `;

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 640 260");
    svg.setAttribute("class", "fuel-line-chart");

    const points = details.points.map((point) => ({
      date: new Date(point.date),
      average: point.average,
    }));

    const width = 640;
    const height = 260;
    const margin = { top: 20, right: 22, bottom: 46, left: 72 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const minPrice = Math.min(...points.map((point) => point.average));
    const maxPrice = Math.max(...points.map((point) => point.average));
    const minDate = points[0]?.date?.getTime() ?? 0;
    const maxDate = points[points.length - 1]?.date?.getTime() ?? 0;
    const priceRange = Math.max(maxPrice - minPrice, 1);
    const dateRange = Math.max(maxDate - minDate, 1);

    const axisColor = "#9a5b00";
    const lineColor = "#f59e0b";

    const axis = document.createElementNS("http://www.w3.org/2000/svg", "g");
    axis.innerHTML = `
      <line x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="${axisColor}" stroke-width="1.5" />
      <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}" stroke="${axisColor}" stroke-width="1.5" />
    `;
    svg.appendChild(axis);

    const dateStep = Math.max(1, Math.floor((points.length - 1) / 5));
    const dateLabelIndexes = Array.from({ length: 6 }, (_, index) => Math.min(index * dateStep, points.length - 1));
    dateLabelIndexes.forEach((index) => {
      const point = points[index];
      const x = margin.left + ((point.date.getTime() - minDate) / dateRange) * innerWidth;
      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", x);
      tick.setAttribute("x2", x);
      tick.setAttribute("y1", height - margin.bottom);
      tick.setAttribute("y2", height - margin.bottom + 6);
      tick.setAttribute("stroke", axisColor);
      svg.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x);
      label.setAttribute("y", height - margin.bottom + 18);
      label.setAttribute("fill", axisColor);
      label.setAttribute("font-size", "10");
      label.setAttribute("text-anchor", "middle");
      label.textContent = point.date.toLocaleDateString("en-AU", { month: "short", day: "numeric" });
      svg.appendChild(label);
    });

    const priceTickValues = [minPrice, (minPrice + maxPrice) / 2, maxPrice];
    priceTickValues.forEach((price) => {
      const y = margin.top + innerHeight - ((price - minPrice) / priceRange) * innerHeight;
      const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
      tick.setAttribute("x1", margin.left - 6);
      tick.setAttribute("x2", margin.left);
      tick.setAttribute("y1", y);
      tick.setAttribute("y2", y);
      tick.setAttribute("stroke", axisColor);
      svg.appendChild(tick);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", margin.left - 10);
      label.setAttribute("y", y + 4);
      label.setAttribute("fill", axisColor);
      label.setAttribute("font-size", "10");
      label.setAttribute("text-anchor", "end");
      label.textContent = `${price.toFixed(1)}`;
      svg.appendChild(label);
    });

    const axisLabelX = document.createElementNS("http://www.w3.org/2000/svg", "text");
    axisLabelX.setAttribute("x", width / 2);
    axisLabelX.setAttribute("y", height - 8);
    axisLabelX.setAttribute("fill", axisColor);
    axisLabelX.setAttribute("font-size", "11");
    axisLabelX.setAttribute("text-anchor", "middle");
    axisLabelX.textContent = "Date";
    svg.appendChild(axisLabelX);

    const axisLabelY = document.createElementNS("http://www.w3.org/2000/svg", "text");
    axisLabelY.setAttribute("x", 14);
    axisLabelY.setAttribute("y", height / 2);
    axisLabelY.setAttribute("fill", axisColor);
    axisLabelY.setAttribute("font-size", "11");
    axisLabelY.setAttribute("text-anchor", "middle");
    axisLabelY.setAttribute("transform", `rotate(-90 14 ${height / 2})`);
    axisLabelY.textContent = "Average price (cents per litre)";
    svg.appendChild(axisLabelY);

    const pathData = points.map((point, index) => {
      const x = margin.left + ((point.date.getTime() - minDate) / dateRange) * innerWidth;
      const y = margin.top + innerHeight - ((point.average - minPrice) / priceRange) * innerHeight;
      return `${index === 0 ? "M" : "L"}${x},${y}`;
    }).join(" ");

    const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
    line.setAttribute("d", pathData);
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", lineColor);
    line.setAttribute("stroke-width", "3");
    svg.appendChild(line);

    const circles = points.map((point, index) => {
      const x = margin.left + ((point.date.getTime() - minDate) / dateRange) * innerWidth;
      const y = margin.top + innerHeight - ((point.average - minPrice) / priceRange) * innerHeight;
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x);
      circle.setAttribute("cy", y);
      circle.setAttribute("r", "3.5");
      circle.setAttribute("fill", lineColor);
      svg.appendChild(circle);
      return circle;
    });

    const prediction = document.createElement("p");
    prediction.className = "fuel-prediction";
    prediction.textContent = `Next predicted price drop: Week of ${mondayLabel}`;

    card.appendChild(title);
    card.appendChild(summary);
    card.appendChild(svg);
    card.appendChild(prediction);
    fuelTrends.innerHTML = "";
    fuelTrends.appendChild(card);
  }

  function formatMondayDate(dateString) {
    const date = new Date(`${dateString}T00:00:00`);
    const day = date.getDay();
    const diffToMonday = day === 0 ? -6 : 1 - day;
    date.setDate(date.getDate() + diffToMonday);
    return date.toLocaleDateString("en-AU", {
      weekday: "long",
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  fetchActivities();
  loadFuelTrends();
});
