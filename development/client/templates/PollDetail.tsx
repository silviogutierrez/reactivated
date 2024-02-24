import React from "react";

import {CSRFToken, reverse, templates} from "@reactivated";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import * as styles from "@client/styles.css";

export const Template = ({error_message, question}: templates.PollDetail) => (
    <Layout title={question.question_text}>
        <form
            action={reverse("vote", {question_id: question.id})}
            method="post"
            className={styles.sprinkles({
                display: "flex",
                gap: 10,
                flexDirection: "column",
            })}
        >
            <CSRFToken />
            <forms.Fieldset>
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
            </forms.Fieldset>
            <div className={styles.sprinkles({display: "flex", gap: 10})}>
                <forms.Button type="submit">Vote</forms.Button>
                <forms.ButtonLink
                    href={reverse("update_poll", {question_id: question.id})}
                >
                    Update poll
                </forms.ButtonLink>
                <forms.ButtonLink
                    href={reverse("poll_comments", {question_id: question.id})}
                >
                    Comments
                </forms.ButtonLink>
            </div>
        </form>
    </Layout>
);
