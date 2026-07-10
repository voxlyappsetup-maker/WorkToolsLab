<?php
/**
 * Plugin Name: WorkToolsLab Author Links
 * Description: Use the canonical author profile in Kadence author links and Rank Math schema.
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Return the canonical author profile URL.
 *
 * @return string
 */
function worktoolslab_author_links_profile_url() {
	return home_url( '/about/hayssam-dennaoui/' );
}

/**
 * Return the author's LinkedIn profile URL.
 *
 * @return string
 */
function worktoolslab_author_links_linkedin_url() {
	return 'https://www.linkedin.com/in/hayssam-dennaoui/';
}

/**
 * Return the canonical WorkToolsLab Organization entity ID.
 *
 * @return string
 */
function worktoolslab_author_links_organization_id() {
	return home_url( '/#organization' );
}

/**
 * Return the canonical WorkToolsLab WebSite entity ID.
 *
 * @return string
 */
function worktoolslab_author_links_website_id() {
	return home_url( '/#website' );
}

/**
 * Tell Kadence to use the Website/profile URL configured
 * on the WordPress user instead of the author archive URL.
 */
add_filter(
	'kadence_author_use_profile_link',
	'__return_true',
	999
);

/**
 * Normalize WorkToolsLab author identity in Rank Math JSON-LD.
 *
 * The dedicated author profile page gets a bounded, explicit graph:
 *
 * Organization -> WebSite
 * ProfilePage -> Person
 *
 * Other pages retain Rank Math's normal graph while Hayssam's Person
 * identity and Article author references are normalized to the canonical
 * author profile URL.
 */
add_filter(
	'rank_math/json_ld',
	static function ( $data, $jsonld ) {
		if ( ! is_array( $data ) ) {
			return $data;
		}

		$profile_url     = worktoolslab_author_links_profile_url();
		$linkedin_url    = worktoolslab_author_links_linkedin_url();
		$organization_id = worktoolslab_author_links_organization_id();
		$website_id      = worktoolslab_author_links_website_id();

		$profile_url_normalized = untrailingslashit( $profile_url );
		$home_url               = home_url( '/' );
		$home_url_normalized    = untrailingslashit( $home_url );

		$author_user = get_user_by( 'slug', 'hayssam-dennaoui' );
		$archive_url = $author_user
			? get_author_posts_url( $author_user->ID )
			: home_url( '/author/hayssam-dennaoui/' );
		$archive_url_normalized = untrailingslashit( $archive_url );

		/*
		 * Dedicated author profile page.
		 *
		 * Build a deterministic ProfilePage graph instead of depending
		 * on another Rank Math entity being present for conversion.
		 */
		$is_author_profile = false;
		$profile_page_id   = 0;

		if ( is_page() ) {
			$profile_page_id = (int) get_queried_object_id();
			$current_url = $profile_page_id
				? get_permalink( $profile_page_id )
				: '';

			$is_author_profile =
				$current_url
				&& untrailingslashit( $current_url ) === $profile_url_normalized;
		}

		if ( $is_author_profile ) {
			$profile_page_entity_id = trailingslashit( $profile_url ) . '#webpage';
			$page_name = get_the_title( $profile_page_id );

			if ( ! $page_name ) {
				$page_name = 'Hayssam Dennaoui | WorkToolsLab Editor & Product Builder';
			}

			$person = array(
				'@type'       => 'Person',
				'@id'         => $profile_url,
				'name'        => 'Hayssam Dennaoui',
				'url'         => $profile_url,
				'jobTitle'    => 'Editor',
				'description' =>
					'Digital product builder and WorkToolsLab editor writing about work-management tools for freelancers and small teams.',
				'worksFor'    => array(
					'@type' => 'Organization',
					'@id'   => $organization_id,
					'name'  => 'WorkToolsLab',
					'url'   => $home_url,
				),
				'sameAs'      => array(
					$linkedin_url,
				),
			);

			if ( $author_user ) {
				$avatar_url = get_avatar_url(
					$author_user->ID,
					array(
						'size' => 96,
					)
				);

				if ( $avatar_url ) {
					$person['image'] = array(
						'@type'      => 'ImageObject',
						'@id'        => $avatar_url,
						'url'        => $avatar_url,
						'caption'    => 'Hayssam Dennaoui',
						'inLanguage' => 'en-US',
					);
				}
			}

			return array(
				'worktoolslab_organization' => array(
					'@type' => 'Organization',
					'@id'   => $organization_id,
					'name'  => 'WorkToolsLab',
					'url'   => $home_url,
				),
				'worktoolslab_website' => array(
					'@type'      => 'WebSite',
					'@id'        => $website_id,
					'url'        => $home_url_normalized,
					'name'       => 'WorkToolsLab',
					'publisher'  => array(
						'@id' => $organization_id,
					),
					'inLanguage' => 'en-US',
				),
				'worktoolslab_author_profile_page' => array(
					'@type'         => 'ProfilePage',
					'@id'           => $profile_page_entity_id,
					'url'           => $profile_url,
					'name'          => $page_name,
					'datePublished' => get_the_date( 'c', $profile_page_id ),
					'dateModified'  => get_the_modified_date( 'c', $profile_page_id ),
					'isPartOf'      => array(
						'@id' => $website_id,
					),
					'inLanguage'    => 'en-US',
					'mainEntity'    => array(
						'@id' => $profile_url,
					),
				),
				'worktoolslab_author_profile_person' => $person,
			);
		}

		/*
		 * All other pages:
		 * normalize Hayssam's existing Person entity and Article author
		 * references without rebuilding Rank Math's normal graph.
		 */
		foreach ( $data as $key => $entity ) {
			if ( ! is_array( $entity ) ) {
				continue;
			}

			$types = isset( $entity['@type'] )
				? (array) $entity['@type']
				: array();

			$entity_name = isset( $entity['name'] )
				? wp_strip_all_tags( (string) $entity['name'] )
				: '';

			$entity_id = isset( $entity['@id'] )
				? untrailingslashit( (string) $entity['@id'] )
				: '';

			$is_hayssam_person =
				in_array( 'Person', $types, true )
				&& (
					'Hayssam Dennaoui' === $entity_name
					|| $archive_url_normalized === $entity_id
					|| $profile_url_normalized === $entity_id
				);

			if ( $is_hayssam_person ) {
				$data[ $key ]['@id']  = $profile_url;
				$data[ $key ]['url']  = $profile_url;
				$data[ $key ]['name'] = 'Hayssam Dennaoui';
				$data[ $key ]['jobTitle'] = 'Editor';
				$data[ $key ]['description'] =
					'Digital product builder and WorkToolsLab editor writing about work-management tools for freelancers and small teams.';
				$data[ $key ]['worksFor'] = array(
					'@type' => 'Organization',
					'@id'   => $organization_id,
					'name'  => 'WorkToolsLab',
					'url'   => $home_url,
				);

				$same_as = isset( $entity['sameAs'] ) && is_array( $entity['sameAs'] )
					? $entity['sameAs']
					: array();

				$same_as = array_filter(
					$same_as,
					static function ( $url ) use (
						$profile_url_normalized,
						$archive_url_normalized,
						$home_url_normalized
					) {
						$url = untrailingslashit( (string) $url );

						return ! in_array(
							$url,
							array(
								$profile_url_normalized,
								$archive_url_normalized,
								$home_url_normalized,
							),
							true
						);
					}
				);

				$same_as[] = $linkedin_url;

				$data[ $key ]['sameAs'] = array_values(
					array_unique( $same_as )
				);
			}

			$is_article =
				in_array( 'Article', $types, true )
				|| in_array( 'BlogPosting', $types, true )
				|| in_array( 'NewsArticle', $types, true );

			if ( $is_article && isset( $entity['author'] ) ) {
				$author = $entity['author'];

				$author_name = is_array( $author ) && isset( $author['name'] )
					? wp_strip_all_tags( (string) $author['name'] )
					: '';

				$author_id = is_array( $author ) && isset( $author['@id'] )
					? untrailingslashit( (string) $author['@id'] )
					: '';

				$is_hayssam_author =
					'Hayssam Dennaoui' === $author_name
					|| $archive_url_normalized === $author_id
					|| $profile_url_normalized === $author_id;

				if ( $is_hayssam_author ) {
					$data[ $key ]['author'] = array(
						'@id'  => $profile_url,
						'name' => 'Hayssam Dennaoui',
					);
				}
			}
		}

		return $data;
	},
	99,
	2
);
