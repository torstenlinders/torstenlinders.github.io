document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#kompass-test");
  const resultBox = document.querySelector("#test-result");
  const resultText = document.querySelector("#test-result-text");
  const currentText = document.querySelector("#test-progress-current");
  const backButton = document.querySelector("#test-back");
  const nextButton = document.querySelector("#test-next");
  const submitButton = document.querySelector("#test-submit");

  if (
    !form ||
    !resultBox ||
    !resultText ||
    !currentText ||
    !backButton ||
    !nextButton ||
    !submitButton
  ) {
    return;
  }

  const questions = [...form.querySelectorAll(".test-question")];
  let currentIndex = 0;

  function hasAnswer(question) {
    return Boolean(question.querySelector("input:checked"));
  }

  function allQuestionsAnswered() {
    return questions.every(hasAnswer);
  }

  function showQuestion(index) {
    questions.forEach((question, questionIndex) => {
      question.hidden = questionIndex !== index;
    });

    currentIndex = index;
    currentText.textContent = String(index + 1);

    backButton.hidden = index === 0;

    const isLastQuestion = index === questions.length - 1;

    nextButton.hidden = isLastQuestion;
    nextButton.disabled = !hasAnswer(questions[index]);

    submitButton.hidden = !isLastQuestion;
    submitButton.disabled = !allQuestionsAnswered();

    questions[index].scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }

  questions.forEach((question) => {
    question.addEventListener("change", () => {
      if (currentIndex === questions.length - 1) {
        submitButton.disabled = !allQuestionsAnswered();
      } else {
        nextButton.disabled = !hasAnswer(questions[currentIndex]);
      }
    });
  });

  nextButton.addEventListener("click", () => {
    if (
      currentIndex < questions.length - 1 &&
      hasAnswer(questions[currentIndex])
    ) {
      showQuestion(currentIndex + 1);
    }
  });

  backButton.addEventListener("click", () => {
    if (currentIndex > 0) {
      showQuestion(currentIndex - 1);
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!allQuestionsAnswered()) {
      return;
    }

    let score = 0;
    let maximum = 0;

    for (const question of questions) {
      const selected = question.querySelector("input:checked");
      const weight = Number(question.dataset.weight || 1);

      score += Number(selected.value) * weight;
      maximum += 2 * weight;
    }

    const normalisedScore = score / maximum;

    const language =
      document.documentElement.lang?.toLowerCase().startsWith("en")
        ? "en"
        : "sv";

    const messages = {
      sv: {
        strong: "Du verkar dela många av Kompass utgångspunkter.",
        some: "Du delar flera av Kompass tankar, men inte alla.",
        limited:
          "Kompass är kanske inte ditt självklara parti, men vi hoppas att samtalet ändå kan vara värdefullt."
      },
      en: {
        strong: "You appear to share many of Kompass's starting points.",
        some: "You share several of Kompass's ideas, although not all of them.",
        limited:
          "Kompass may not be your obvious choice, but we hope the conversation can still be worthwhile."
      }
    };

    let resultLevel;

    if (normalisedScore >= 0.4) {
      resultLevel = "strong";
    } else if (normalisedScore >= 0.0) {
      resultLevel = "some";
    } else {
      resultLevel = "limited";
    }

    form.hidden = true;
    resultText.textContent = messages[language][resultLevel];
    resultBox.hidden = false;

    resultBox.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  });

  showQuestion(0);
});