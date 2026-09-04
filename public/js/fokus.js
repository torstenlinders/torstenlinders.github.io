document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#fokus-form");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const answers = {};

    const questions = form.querySelectorAll(".fokus-question");

    questions.forEach((question) => {
      const type = question.dataset.type;
      const name = question.dataset.id;

      if (type === "radio") {
        const selected = question.querySelector(
          `input[name="${name}"]:checked`
        );

        answers[name] = selected ? selected.value : null;
      }

      else if (type === "checkbox") {
        const selected = question.querySelectorAll(
          `input[name="${name}"]:checked`
        );

        answers[name] = Array.from(selected).map(
          (input) => input.value
        );
      }

      else if (type === "text") {
        const textarea = question.querySelector(
          `textarea[name="${name}"]`
        );

        answers[name] = textarea
          ? textarea.value.trim()
          : "";
      }
    });

    console.log("Fokus answers:", answers);

    try {
      const response = await fetch("/api/fokus", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(answers)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      console.log("Server response:", result);

    } catch (error) {
      console.error("Kunde inte skicka svar:", error);
    }

  });
});