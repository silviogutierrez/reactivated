import React from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types, reverse} from "@client/generated";

export default ({error_message, question}: Types["PollDetailProps"]) => (
    <Layout title={question.question_text}>
        <form action={reverse("vote", {question_id: question.id})} method="post">
            <CSRFToken />
            <fieldset>
                <legend>
                    <h1>{question.question_text}</h1>
                </legend>
                {error_message != null && (
                    <p>
                        <strong>{error_message}</strong>
                    </p>
                )}
                {question.choices.map((choice, counter) => (
                    <React.Fragment key={choice.id}>
                        <input
                            type="radio"
                            name="choice"
                            id={`choice${counter}`}
                            value={choice.id}
                        />
                        <label htmlFor={`choice${counter}`}>{choice.choice_text}</label>
                        <br />
                    </React.Fragment>
                ))}
            </fieldset>
            <input type="submit" value="Vote" />
        </form>
    </Layout>
);
