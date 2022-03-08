import React from "react";

import {CSRFToken, templates, reverse} from "@reactivated";

import {css} from "@linaria/core";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import * as styles from "@client/styles";

export default ({error_message, question}: templates.PollDetail) => (
    <Layout title={question.question_text}>
        <form
            action={reverse("vote", {question_id: question.id})}
            method="post"
            className={css`
                ${styles.verticallySpaced(10)}
            `}
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
            <div className={styles.horizontallySpaced}>
                <forms.Button type="submit">Vote</forms.Button>
                <forms.ButtonLink
                    href={reverse("update_poll", {question_id: question.id})}
                >
                    Update poll
                </forms.ButtonLink>
            </div>
        </form>
    </Layout>
);
