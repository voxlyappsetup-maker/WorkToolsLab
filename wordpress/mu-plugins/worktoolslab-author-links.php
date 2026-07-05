<?php
/**
 * Plugin Name: WorkToolsLab Author Links
 * Description: Kadence profile links + Rank Math JSON-LD author identity for Hayssam Dennaoui.
 * Version: 1.1.0
 *
 * Live path: wp-content/mu-plugins/worktoolslab-author-links.php
 * Repository mirror — manual deployment only. See docs/WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'WORKTOOLSLAB_AUTHOR_PROFILE_URL', 'https://worktoolslab.com/about/hayssam-dennaoui/' );
define( 'WORKTOOLSLAB_AUTHOR_LINKEDIN_URL', 'https://www.linkedin.com/in/hayssam-dennaoui/' );
define( 'WORKTOOLSLAB_AUTHOR_SLUG', 'hayssam-dennaoui' );

/**
 * Use WordPress user website URL for Kadence author/profile links when enabled.
 */
function worktoolslab_kadence_author_use_profile_link( $use_profile_link ) {
	return true;
}
add_filter( 'kadence_author_use_profile_link', 'worktoolslab_kadence_author_use_profile_link' );

/**
 * Normalize Rank Math JSON-LD for Hayssam Dennaoui and profile page.
 *
 * @param array  $data   Schema graph or entity.
 * @param object $jsonld Rank Math JSON-LD helper instance.
 * @return array
 */
function worktoolslab_rank_math_json_ld( $data, $jsonld ) {
	if ( ! is_array( $data ) ) {
		return $data;
	}

	$profile_url = WORKTOOLSLAB_AUTHOR_PROFILE_URL;
	$linkedin    = WORKTOOLSLAB_AUTHOR_LINKEDIN_URL;
	$person_id   = $profile_url;

	$is_profile_page = is_page() && WORKTOOLSLAB_AUTHOR_SLUG === get_post_field( 'post_name', get_queried_object_id() );

	if ( isset( $data['@graph'] ) && is_array( $data['@graph'] ) ) {
		foreach ( $data['@graph'] as $index => $entity ) {
			$data['@graph'][ $index ] = worktoolslab_normalize_schema_entity( $entity, $person_id, $profile_url, $linkedin, $is_profile_page );
		}
		return $data;
	}

	return worktoolslab_normalize_schema_entity( $data, $person_id, $profile_url, $linkedin, $is_profile_page );
}
add_filter( 'rank_math/json_ld', 'worktoolslab_rank_math_json_ld', 99, 2 );

/**
 * Normalize a single schema entity or graph node.
 *
 * @param array  $entity          Schema entity.
 * @param string $person_id       Canonical @id for Hayssam Person.
 * @param string $profile_url       Profile page URL.
 * @param string $linkedin          LinkedIn sameAs URL.
 * @param bool   $is_profile_page   Whether current request is the profile page.
 * @return array
 */
function worktoolslab_normalize_schema_entity( $entity, $person_id, $profile_url, $linkedin, $is_profile_page ) {
	if ( ! is_array( $entity ) ) {
		return $entity;
	}

	$types = isset( $entity['@type'] ) ? (array) $entity['@type'] : array();

	if ( in_array( 'Person', $types, true ) && worktoolslab_is_hayssam_person_entity( $entity ) ) {
		$entity['@id']      = $person_id;
		$entity['url']      = $profile_url;
		$entity['name']     = 'Hayssam Dennaoui';
		$entity['jobTitle'] = 'Editor';
		$entity['sameAs']   = array( $linkedin );
		$entity['worksFor'] = array(
			'@type' => 'Organization',
			'name'  => 'WorkToolsLab',
			'url'   => home_url( '/' ),
		);
	}

	$article_types = array( 'BlogPosting', 'Article', 'NewsArticle' );
	if ( array_intersect( $article_types, $types ) && isset( $entity['author'] ) ) {
		$entity['author'] = array(
			'@id'   => $person_id,
			'@type' => 'Person',
			'name'  => 'Hayssam Dennaoui',
			'url'   => $profile_url,
		);
	}

	if ( $is_profile_page && in_array( 'WebPage', $types, true ) ) {
		$entity['@type']      = 'ProfilePage';
		$entity['mainEntity'] = array(
			'@type' => 'Person',
			'@id'   => $person_id,
			'name'  => 'Hayssam Dennaoui',
			'url'   => $profile_url,
		);
	}

	if ( $is_profile_page && in_array( 'ProfilePage', $types, true ) ) {
		$entity['mainEntity'] = array(
			'@type' => 'Person',
			'@id'   => $person_id,
			'name'  => 'Hayssam Dennaoui',
			'url'   => $profile_url,
		);
	}

	return $entity;
}

/**
 * Detect Hayssam Dennaoui Person nodes emitted by Rank Math or archives.
 *
 * @param array $entity Schema entity.
 * @return bool
 */
function worktoolslab_is_hayssam_person_entity( $entity ) {
	if ( empty( $entity['@type'] ) || ! in_array( 'Person', (array) $entity['@type'], true ) ) {
		return false;
	}

	$name = isset( $entity['name'] ) ? (string) $entity['name'] : '';
	if ( 'Hayssam Dennaoui' === $name ) {
		return true;
	}

	$url = isset( $entity['url'] ) ? (string) $entity['url'] : '';
	if ( false !== strpos( $url, WORKTOOLSLAB_AUTHOR_SLUG ) ) {
		return true;
	}

	$id = isset( $entity['@id'] ) ? (string) $entity['@id'] : '';
	if ( false !== strpos( $id, WORKTOOLSLAB_AUTHOR_SLUG ) ) {
		return true;
	}

	return false;
}

/**
 * Ensure Person entity exists on dedicated profile page graph when missing.
 *
 * @param array $data Schema data.
 * @return array
 */
function worktoolslab_ensure_profile_page_person( $data ) {
	if ( ! is_page() || WORKTOOLSLAB_AUTHOR_SLUG !== get_post_field( 'post_name', get_queried_object_id() ) ) {
		return $data;
	}

	if ( ! isset( $data['@graph'] ) || ! is_array( $data['@graph'] ) ) {
		return $data;
	}

	foreach ( $data['@graph'] as $entity ) {
		if ( is_array( $entity ) && worktoolslab_is_hayssam_person_entity( $entity ) && WORKTOOLSLAB_AUTHOR_PROFILE_URL === ( $entity['@id'] ?? '' ) ) {
			return $data;
		}
	}

	$data['@graph'][] = array(
		'@type'     => 'Person',
		'@id'       => WORKTOOLSLAB_AUTHOR_PROFILE_URL,
		'name'      => 'Hayssam Dennaoui',
		'url'       => WORKTOOLSLAB_AUTHOR_PROFILE_URL,
		'jobTitle'  => 'Editor',
		'sameAs'    => array( WORKTOOLSLAB_AUTHOR_LINKEDIN_URL ),
		'worksFor'  => array(
			'@type' => 'Organization',
			'name'  => 'WorkToolsLab',
			'url'   => home_url( '/' ),
		),
	);

	return $data;
}
add_filter( 'rank_math/json_ld', 'worktoolslab_ensure_profile_page_person', 100, 1 );
