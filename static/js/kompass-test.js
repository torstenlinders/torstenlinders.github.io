document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#kompass-test");
  const resultBox = document.querySelector("#test-result");
  const resultText = document.querySelector("#test-result-text");
  const currentText = document.querySelector("#test-progress-current");
  const backButton = document.querySelector("#test-back");
  const nextButton = document.querySelector("#test-next");

  if (
      !form ||
      !resultBox ||
      !resultText ||
      !currentText ||
      !backButton ||
      !nextButton 
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

  const language =
    document.documentElement.lang?.toLowerCase().startsWith("en")
      ? "en"
      : "sv";

  function showQuestion(index) {
    questions.forEach((question, questionIndex) => {
      question.hidden = questionIndex !== index;
    });

    currentIndex = index;
    currentText.textContent = String(index + 1);

    backButton.hidden = index === 0;

    const isLastQuestion = index === questions.length - 1;

    nextButton.hidden = false;

    if (isLastQuestion) {
        nextButton.textContent = window.kompassI18n.result;
    } else {
        nextButton.textContent = window.kompassI18n.next;
    }

    nextButton.disabled = !hasAnswer(questions[index]);

    questions[index].scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }

    questions.forEach((question) => {
    question.addEventListener("change", () => {
        nextButton.disabled = !hasAnswer(questions[currentIndex]);
    });
    });

    nextButton.addEventListener("click", () => {
        if (!hasAnswer(questions[currentIndex])) {
            return;
        }
        if (currentIndex === questions.length - 1) {
            form.requestSubmit();
            return;
        }
        showQuestion(currentIndex + 1);
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

    let message;

    if (resultLevel === "strong") {
    message = window.kompassI18n.strong;
    } else if (resultLevel === "some") {
    message = window.kompassI18n.some;
    } else {
    message = window.kompassI18n.limited;
    }

    resultText.textContent = message;

    form.hidden = true;
    resultBox.hidden = false;

    resultBox.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  });

  showQuestion(0);
});