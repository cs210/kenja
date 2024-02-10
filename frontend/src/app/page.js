"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function Home() {
  // State for holding user query
  const [query, setQuery] = useState("");

  // Update action on search
  function search(formData) {
    const query = formData.get("query");
    setQuery(query);
  }

  // Simple front-end that has a search bar and allows you to look at stuff
  return (
    <main className={styles.main}>
      <div>
        <h1>Sommelier</h1>
        <p>You give us a description, we give you wine recs.</p>
        <br />
        <form action={search}>
          <input name="query"></input>
          <br />
          <button type="submit">Submit</button>
        </form>
        <p>
        { query !== "" ? <><br /><p> Q: { query } </p></> : "" }
        </p>
      </div>
    </main>
  );
}
