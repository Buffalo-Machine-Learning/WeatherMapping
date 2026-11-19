const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getHealth() {
  const response = await fetch(
    `${API_BASE_URL}/health`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to connect to API"
    );
  }

  return response.json();
}

export async function getForecastTimes() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/forecast/times`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load forecast times"
    );
  }

  return response.json();
}