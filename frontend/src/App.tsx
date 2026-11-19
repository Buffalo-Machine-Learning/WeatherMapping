import { useEffect, useState } from "react";

import { getHealth, getForecastTimes } from "./api/weather";


function App() {
  const [status, setStatus] = useState(
    "Checking..."
  );

  const [times, setTimes] = useState(
    "Checking..."
  );


  useEffect(() => {

    async function checkApi() {
      try {
        const data = await getHealth();

        setStatus(data.status);

      } catch {
        setStatus("API unavailable");
      }
    }

    async function getForecast() {
      try {
        const data = await getForecastTimes();

        setTimes(data.times);

      } catch {
        setTimes("API unavailable");
      }
    }


    checkApi();
    getForecast();

  }, []);


  return (
    <div>
      <h1>WeatherMapping</h1>

      <p>
        API status: {status}
        Forecast times: {times}
      </p>
    </div>
  );
}


export default App;