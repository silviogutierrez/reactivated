import React from "react";

import {Types} from "@reactivated";

import {css} from "@linaria/core";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import * as styles from "@client/styles";

export default (props: Types["PollsIndexProps"]) => (
    <Layout
        title="Polls"
        className={css`
            ${styles.verticallySpaced(10)}
        `}
    >
        <h1>Polls</h1>
        {props.latest_question_list.length > 0 ? (
            <ul className={css``}>
                {props.latest_question_list.map((question) => (
                    <li key={question.id}>
                        <a href={`/polls/${question.id}`}>{question.question_text}</a>
                    </li>
                ))}
            </ul>
        ) : (
            <p>No polls are available.</p>
        )}
        <forms.ButtonLink href="/polls/create/">Create a new question</forms.ButtonLink>
    </Layout>
);
